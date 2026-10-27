import io
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import pandas as pd
from azure.core.exceptions import ResourceExistsError, HttpResponseError
from portfolio.importer import parse_number, normalize, read_uploaded_file, read_file_path
from portfolio.analyzer import analyze_portfolio
from portfolio.storage import save_uploaded_file_if_configured


class ImportTests(unittest.TestCase):
    def test_common_number_formats(self):
        cases = {"CHF 1'234.50": 1234.5, "EUR 1.234,50": 1234.5,
                 "USD 1,234.50": 1234.5, "1’234,50": 1234.5,
                 "(120.50)": -120.5, "1e3": 1000, "-12,5": -12.5, "1,234,567": 1234567, "1.234.567": 1234567}
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_number(raw), expected)

    def test_malformed_numbers_are_rejected(self):
        for raw in ["wrong12", "1-2", "--1", "1e309", math.inf, "1,2.3", "12.34,56", "1.2.3"]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_number(raw)

    def test_missing_number_remains_missing(self):
        for raw in [None, float('nan'), "", " "]:
            self.assertIsNone(parse_number(raw))

    def test_csv_delimiters_and_decimal_comma(self):
        for content in ["name;quantity;value\nBond;2;1.234,50\n",
                        "name\tquantity\tvalue\nBond\t2\t1234.5\n",
                        "name,quantity,value\nBond,2,1234.5\n"]:
            with self.subTest(content=content):
                uploaded = io.BytesIO(content.encode())
                uploaded.name = "depot.csv"
                frame = read_uploaded_file(uploaded)
                self.assertEqual(frame.iloc[0]['value'], 1234.5)

    def test_numeric_error_is_not_hidden_by_separator_retry(self):
        uploaded = io.BytesIO(b'name,quantity,value\nBond,1,broken\n')
        uploaded.name = 'depot.csv'
        with self.assertRaisesRegex(ValueError, 'Invalid numeric'):
            read_uploaded_file(uploaded)

    def test_blank_names_are_not_imported_as_nan(self):
        frame = normalize(pd.DataFrame({'name': [None, ' ', 'Bond'],
                                        'quantity': [1, 1, 2], 'value': [5, 10, 20]}))
        self.assertEqual(frame['name'].tolist(), ['Bond'])

    def test_empty_positions_fail_clearly(self):
        with self.assertRaisesRegex(ValueError, 'No valid positions'):
            normalize(pd.DataFrame({'name': [' '], 'quantity': [1], 'value': [10]}))

    def test_optional_fields_do_not_become_nan_strings(self):
        frame = normalize(pd.DataFrame({'name': ['Bond'], 'quantity': [1], 'value': [10],
                                        'currency': [None], 'ticker': [None]}))
        self.assertEqual(frame.iloc[0]['currency'], '')
        self.assertEqual(frame.iloc[0]['ticker'], '')

    def test_duplicate_headers_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate column'):
            normalize(pd.DataFrame([[1, 2, 3, 4]], columns=['Name', 'NAME', 'quantity', 'value']))

    def test_csv_duplicate_headers_are_not_hidden_by_pandas(self):
        uploaded = io.BytesIO(b'name,name,quantity,value\nA,B,1,20\n')
        uploaded.name = 'depot.csv'
        with self.assertRaisesRegex(ValueError, 'Duplicate column'):
            read_uploaded_file(uploaded)

    def test_invalid_pdf_fails_with_validation_error(self):
        uploaded = io.BytesIO(b'not a PDF')
        uploaded.name = 'bad.pdf'
        with self.assertRaisesRegex(ValueError, 'PDF could not be parsed'):
            read_uploaded_file(uploaded)

    def test_unsupported_extension_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported file type'):
            read_file_path(Path('depot.xlsx'))


class AnalysisTests(unittest.TestCase):
    def test_sample_regression(self):
        result = analyze_portfolio(read_file_path(Path(__file__).resolve().parents[1] / 'samples/sample_depot.csv'))
        self.assertEqual(len(result.positions), 8)
        self.assertEqual(result.total_value, 16700)
        self.assertAlmostEqual(result.positions['weight_pct'].sum(), 100)
        self.assertEqual(result.top5.iloc[0]['ticker'], 'NVDA')

    def test_mixed_currencies_rejected(self):
        frame = normalize(pd.DataFrame({'name': ['A', 'B'], 'quantity': [1, 1],
                                        'value': [10, 20], 'currency': ['eur', 'USD']}))
        with self.assertRaisesRegex(ValueError, 'Mixed currencies'):
            analyze_portfolio(frame)

    def test_same_currency_case_insensitive(self):
        frame = normalize(pd.DataFrame({'name': ['A', 'B'], 'quantity': [1, 1],
                                        'value': [10, 20], 'currency': ['eur', ' EUR ']}))
        self.assertEqual(analyze_portfolio(frame).total_value, 30)

    def test_empty_or_nonpositive_portfolio_rejected(self):
        with self.assertRaisesRegex(ValueError, 'No positions'):
            analyze_portfolio(pd.DataFrame())
        frame = pd.DataFrame({'name': ['A'], 'value': [0]})
        with self.assertRaisesRegex(ValueError, 'positive'):
            analyze_portfolio(frame)

    def test_nonfinite_values_rejected(self):
        for value in [math.inf, math.nan]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'finite'):
                analyze_portfolio(pd.DataFrame({'name': ['A'], 'value': [value]}))


class StorageTests(unittest.TestCase):
    def uploaded(self):
        source = io.BytesIO(b'name,quantity,value\nA,1,10\n')
        source.name = '../depot.csv'
        return source

    @patch.dict('os.environ', {}, clear=True)
    def test_unconfigured_storage_skipped(self):
        self.assertIsNone(save_uploaded_file_if_configured(self.uploaded()))

    @patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test'}, clear=True)
    @patch('portfolio.storage.BlobServiceClient')
    def test_uploads_are_unique_and_do_not_overwrite(self, factory):
        client = factory.from_connection_string.return_value
        container = client.get_container_client.return_value
        container.create_container.side_effect = ResourceExistsError('exists')
        source = self.uploaded()
        save_uploaded_file_if_configured(source)
        save_uploaded_file_if_configured(source)
        names = [call.args[0] for call in container.get_blob_client.call_args_list]
        self.assertEqual(len(set(names)), 2)
        self.assertTrue(all('/' not in name for name in names))
        self.assertEqual(source.tell(), 0)
        for call in container.get_blob_client.return_value.upload_blob.call_args_list:
            self.assertFalse(call.kwargs['overwrite'])
        self.assertEqual(client.close.call_count, 2)

    @patch.dict('os.environ', {'AZURE_STORAGE_CONNECTION_STRING': 'test'}, clear=True)
    @patch('portfolio.storage.BlobServiceClient')
    def test_permission_failure_not_swallowed(self, factory):
        client = factory.from_connection_string.return_value
        container = client.get_container_client.return_value
        container.create_container.side_effect = HttpResponseError('forbidden')
        source = self.uploaded()
        with self.assertRaises(HttpResponseError):
            save_uploaded_file_if_configured(source)
        container.get_blob_client.assert_not_called()
        self.assertEqual(source.tell(), 0)
        client.close.assert_called_once()

    @patch.dict('os.environ', {'AZURE_STORAGE_ACCOUNT_URL': 'https://example.invalid'}, clear=True)
    @patch('portfolio.storage.DefaultAzureCredential')
    @patch('portfolio.storage.BlobServiceClient')
    def test_upload_failure_closes_resources_and_rewinds(self, factory, credential):
        client = factory.return_value
        blob = client.get_container_client.return_value.get_blob_client.return_value
        blob.upload_blob.side_effect = HttpResponseError('failed')
        source = self.uploaded()
        with self.assertRaises(HttpResponseError):
            save_uploaded_file_if_configured(source)
        self.assertEqual(source.tell(), 0)
        credential.return_value.close.assert_called_once()
        client.close.assert_called_once()


class IntegrationTests(unittest.TestCase):
    def test_pdf_table_import_and_analysis(self):
        fixture = Path(__file__).resolve().parent / 'fixtures/depot.pdf'
        result = analyze_portfolio(read_file_path(fixture))
        self.assertEqual(len(result.positions), 2)
        self.assertEqual(result.total_value, 200)

    def test_streamlit_renders_complete_sample(self):
        from streamlit.testing.v1 import AppTest
        sample = Path(__file__).resolve().parents[1] / 'samples/sample_depot.csv'
        source = io.BytesIO(sample.read_bytes())
        source.name = 'sample_depot.csv'
        with patch('streamlit.file_uploader', return_value=source), \
             patch('portfolio.storage.save_uploaded_file_if_configured', return_value=None):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app/app.py')).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual([item.value for item in app.metric], ['16,700.00', '8', '25.1%'])
        self.assertEqual(len(app.dataframe), 2)


class CliTests(unittest.TestCase):
    def test_importing_cli_has_no_side_effect(self):
        import importlib
        with patch('sys.stdout', new_callable=io.StringIO) as output:
            module = importlib.import_module('cli')
        self.assertTrue(callable(module.main))
        self.assertEqual(output.getvalue(), '')

    def test_usage_and_missing_file_fail_clearly(self):
        from cli import main
        with patch('sys.stderr', new_callable=io.StringIO) as error:
            self.assertEqual(main([]), 1)
            self.assertIn('Usage:', error.getvalue())
        with patch('sys.stderr', new_callable=io.StringIO) as error:
            self.assertEqual(main(['/does-not-exist.csv']), 1)
            self.assertIn('Processing failed:', error.getvalue())
            self.assertNotIn('Traceback', error.getvalue())
