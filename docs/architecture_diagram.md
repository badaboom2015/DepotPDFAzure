# Example Azure Depot PDF - Architektur

Die Diagramme beschreiben den aktuellen Code und die bereitgestellte Infrastruktur. Eine Ressource in Azure bedeutet nicht automatisch, dass die Anwendung sie bereits verwendet.

## Aktiver Anwendungspfad

```mermaid
flowchart TB
    Browser[Browser mit Streamlit-Sitzung] -->|HTTPS und WebSocket| App[Azure Container Apps: Streamlit]
    ACR[Azure Container Registry] -->|Image beim Start| App
    App -->|Datei hochladen| Blob[Privater Blob-Container uploads]
    App --> Import[CSV lesen oder PDF-Tabellen extrahieren]
    Import --> Pandas[pandas: Kennzahlen und Konzentrationen]
    Pandas --> Summary[Regelbasierte Zusammenfassung]
    Summary --> App
    Identity[Zugewiesene Managed Identity] -. AcrPull und Blob-Rolle .-> App
    App --> Logs[Container-Logs in Log Analytics]
```

Die App speichert einen Upload vor der Analyse in Blob Storage, sofern der Azure-Zugriff konfiguriert ist. Der Browser erhält die Ergebnisse über Streamlit. Der Zugriff auf den Blob-Container erfordert Authentifizierung.

## Bereitgestellte Netzwerk- und Erweiterungsstruktur

```mermaid
flowchart TB
    Public[Öffentlicher HTTPS-Endpunkt] --> App
    subgraph VNet[Azure Virtual Network]
        subgraph Apps[Container-Apps-Subnetz]
            App[Container App: eine Instanz]
        end
        subgraph PE[Subnetz für Private Endpoints]
            BlobPE[Blob Private Endpoint]
            VaultPE[Key Vault Private Endpoint]
        end
        subgraph DB[Delegiertes PostgreSQL-Subnetz]
            Postgres[PostgreSQL 16]
        end
        DNS[Private DNS-Zonen und VNet-Links]
        App -->|Aktiver Storage-Zugriff| BlobPE
        DNS -. Namensauflösung .-> BlobPE
        DNS -. Namensauflösung .-> VaultPE
        DNS -. Namensauflösung .-> Postgres
    end
    BlobPE --> Blob[Azure Blob Storage]
    VaultPE --> Vault[Azure Key Vault]
    Bus[Service Bus: Import-Queue]
    Insights[Application Insights]
    Terraform[Terraform] -. Bereitstellung .-> VNet
    Terraform -. Bereitstellung .-> Bus
    Terraform -. Bereitstellung .-> Insights
```

**Noch ohne fachliche Integration:** PostgreSQL, Service Bus und Key Vault. Application Insights ist bereitgestellt, aber der Python-Code sendet noch keine instrumentierten Anwendungstraces. Deshalb zeigen die Diagramme keine aktiven Analyseverbindungen zu diesen Diensten.

**Netzwerkgrenzen:** PostgreSQL und Key Vault haben keinen öffentlichen Netzwerkzugriff. Blob Storage hat einen Private Endpoint und einen weiterhin aktivierten öffentlichen Endpunkt für die Verwaltung durch Terraform. Anonyme Zugriffe sind deaktiviert. Die Weboberfläche ist öffentlich und hat noch keine Benutzeranmeldung.

**Skalierung:** Single Revision, eine Instanz mit 0,5 vCPU und 1 GiB RAM. Eine spätere Skalierung auf mehrere Instanzen benötigt ein Konzept für Streamlit-Sitzungen und Datei-Uploads.

## Zeitlicher Ablauf eines Dateiimports

```mermaid
sequenceDiagram
    actor User as Benutzer
    participant Browser
    participant App as Streamlit-App
    participant Blob as Blob Storage
    participant Import as Importer
    participant Analyse as Analyzer
    User->>Browser: CSV oder PDF auswählen
    Browser->>App: Datei hochladen
    opt Storage-Zugriff ist konfiguriert
        App->>Blob: Originaldatei mit Authentifizierung speichern
        Blob-->>App: Blob-URI
    end
    App->>Import: Datei lesen und normalisieren
    alt Import erfolgreich
        Import-->>App: Normalisierte Positionen
        App->>Analyse: Kennzahlen und Konzentrationen berechnen
        Analyse-->>App: AnalysisResult
        Note over App: Regelbasierte Textzusammenfassung erstellen
        App-->>Browser: Tabellen, Kennzahlen und Hinweise
    else Datei nicht auswertbar
        Import-->>App: Fehler
        App-->>Browser: Fehlermeldung anzeigen
        Note over App,Blob: Ein bereits gespeicherter Upload bleibt vorhanden
    end
```

Schlägt die konfigurierte Blob-Speicherung fehl, erreicht die Ausführung den Importer nicht. Die App zeigt den Fehler an. Das Diagramm beschreibt den Webpfad; die CLI liest lokale Dateien ohne Blob-Speicherung.

Die [ausführliche Architekturbeschreibung](architecture.md) erklärt Komponenten, Datenhaltung, Identitäten, Netzwerkadressen und Betrieb.
