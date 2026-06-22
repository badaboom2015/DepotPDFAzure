from dataclasses import dataclass
from typing import List
import pandas as pd

@dataclass
class AnalysisResult:
    positions: pd.DataFrame
    top5: pd.DataFrame
    total_value: float
    max_weight: float
    risks: List[str]
    warnings: List[str]
