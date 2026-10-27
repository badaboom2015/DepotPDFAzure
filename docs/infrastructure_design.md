# Example Azure Depot PDF - Infrastruktur und Betrieb

## Architektur

Die [Architekturdiagramme](architecture_diagram.md) unterscheiden den aktiven Anwendungspfad von den bereitgestellten Erweiterungsdiensten. Terraform verwaltet die Azure-Ressourcen. GitHub Actions prüft den Container-Build und die CLI, während das Deployment über `scripts/deploy-azure.sh` erfolgt.

## Container-Betrieb

Die Streamlit-Anwendung läuft in einem Consumption-Workload-Profil von Azure Container Apps. Das zugehörige Subnetz ist an `Microsoft.App/environments` delegiert. Die App verwendet Single Revision und genau eine Instanz mit 0,5 vCPU und 1 GiB RAM. Diese Begrenzung hält Streamlit-Sitzungen und Upload-Anfragen auf derselben Instanz.

Das Image liegt in Azure Container Registry Basic. Der Build erfolgt remote für Linux/AMD64. Der öffentliche HTTPS-Endpunkt bleibt bei einem Versionswechsel stabil. Streamlit stellt unter `/_stcore/health` einen Healthcheck bereit.

## Netzwerk und Identität

Das virtuelle Netzwerk enthält separate Subnetze für Container Apps, Private Endpoints und PostgreSQL. Private DNS-Zonen mit VNet-Links unterstützen die Namensauflösung der privaten Dienste.

Eine zugewiesene Managed Identity erhält `AcrPull`, `Storage Blob Data Contributor` und `Key Vault Secrets User`. Die Anwendung wählt diese Identität mit `AZURE_CLIENT_ID`. Registry- und Blob-Zugriff nutzen dadurch keine im Code hinterlegten Zugriffsschlüssel. Die Key-Vault-Rolle bereitet eine spätere Secret-Nutzung vor.

| Dienst | Netzwerkzugriff | Nutzung durch die Anwendung |
| --- | --- | --- |
| Blob Storage | Private Endpoint vorhanden. Öffentlicher Endpunkt für Terraform-Verwaltung aktiv, anonymer Zugriff deaktiviert. | Uploads speichern. |
| PostgreSQL Flexible Server | Privates, delegiertes Subnetz und Private DNS. Öffentlicher Zugriff deaktiviert. | Noch keine Datenbankintegration. |
| Key Vault | Private Endpoint, RBAC und deaktivierter öffentlicher Netzwerkzugriff. | Noch keine Secret-Abfrage im Anwendungscode. |
| Service Bus Standard | Namespace und Queue bereitgestellt. Kein Private Endpoint konfiguriert. | Noch kein Producer oder Worker. |

Die öffentliche Weboberfläche hat noch keine Benutzeranmeldung. Vor dem Einsatz mit vertraulichen Depotdateien sind ein passendes Authentifizierungs- und Berechtigungskonzept sowie Regeln für Aufbewahrung und Löschung erforderlich.

## Daten und Erweiterungen

Der Import und die Analyse laufen synchron in der Streamlit-Anwendung. PostgreSQL 16 mit B1ms und 32 GiB Speicher sowie die Service-Bus-Queue sind für spätere Erweiterungen vorhanden. Ein möglicher nächster Ausbauschritt ist ein Worker, der Nachrichten verarbeitet und Analyseergebnisse in PostgreSQL speichert. Dieser Ablauf ist noch nicht implementiert.

## Beobachtbarkeit

Die Container-Apps-Umgebung verwendet Log Analytics für Container-Logs. Ein Azure-Monitor-Metrikalarm verfolgt unerwartete Neustarts. Application Insights ist ebenfalls bereitgestellt, und seine Connection String steht der App zur Verfügung. Eine SDK-Instrumentierung des Python-Codes fehlt noch. Der Action Group sind keine konkreten Benachrichtigungsempfänger zugeordnet.

## Deployment und State

Das Deployment-Skript erstellt zuerst die Registry, baut ein versioniertes Image und wendet anschließend den vollständigen Terraform-Plan an. Es bestätigt das Apply automatisch. Die aktuelle Umgebung verwendet den Workspace `azure-depot-pdf`.

State und lokale Variablen bleiben außerhalb von Git. Der State enthält das generierte Datenbankpasswort und benötigt eine geschützte Sicherung. Der historische Workspace `default` gehört zur alten Subscription. Für Teamarbeit sollte ein Remote-Backend mit Zugriffsschutz und State-Locking eingerichtet werden.

Die JSON-Dateien im Terraform-Verzeichnis sind historische Referenzen mit angepassten Namen und ersetzen keine Abfrage der aktuellen Azure-Ressourcen.
