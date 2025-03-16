# Zonnepanelen Check

Een applicatie om de overproductie van zonnepanelen te analyseren en de theoretische opbrengst te berekenen bij verschillende opties voor energieopslag.

![Zonnepanelen Check](https://via.placeholder.com/800x400?text=Zonnepanelen+Check)

## 📝 Beschrijving

Zonnepanelen Check analyseert historische gegevens over energieproductie en -verbruik van zonnepanelen om te berekenen welke opslagopties het meest rendabel zijn. De applicatie helpt bij het nemen van beslissingen over investeringen in energieopslag, zoals warmwaterboilers of thuisbatterijen.

### Belangrijkste functies:
- Inladen en analyseren van historische energiedata (CSV-formaat)
- Berekenen van opslag in warmwaterboiler en de bijbehorende gasbesparing
- Berekenen van opslag in accu en de bijbehorende kostenbesparing
- Visualiseren van energieproductie, -verbruik en -opslag
- Vergelijken van verschillende opslagopties
- Configureerbare parameters voor nauwkeurige berekeningen

## 🚀 Installatie

### Vereisten
- Python 3.8 of hoger
- pip (Python package manager)

### Virtual Environment aanmaken (aanbevolen)

Het is aanbevolen om een virtuele omgeving te gebruiken voor deze applicatie om pakketconflicten te voorkomen.

#### Windows
```bash
# Aanmaken van de virtuele omgeving
python -m venv venv

# Activeren van de virtuele omgeving
venv\Scripts\activate

# Je terminal moet nu (venv) tonen aan het begin van de regel
```

#### macOS / Linux
```bash
# Aanmaken van de virtuele omgeving
python3 -m venv venv

# Activeren van de virtuele omgeving
source venv/bin/activate

# Je terminal moet nu (venv) tonen aan het begin van de regel
```

### Installatiestappen

1. Clone deze repository:
```bash
git clone https://github.com/Fbeunder/Zonnepanelen_check.git
cd Zonnepanelen_check
```

2. Maak een virtuele omgeving aan en activeer deze (zie hierboven)

3. Installeer de benodigde packages:
```bash
pip install -r requirements.txt
```

4. Deactiveren van de virtuele omgeving (wanneer je klaar bent):
```bash
deactivate
```

## 🔧 Gebruik

Activeer eerst de virtuele omgeving (indien gebruikt) en start de applicatie:

```bash
# Activeer de virtuele omgeving (indien nodig)
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Start de applicatie
streamlit run app.py
```

De webinterface is nu beschikbaar op http://localhost:8501

### CSV-bestandsformaat
Upload een CSV-bestand met de volgende kolommen:
```
Date/Time,Energy Produced (Wh),Energy Consumed (Wh),Exported to Grid (Wh),Imported from Grid (Wh)
03/01/2024 00:00,0,81,0,81
03/01/2024 00:15,0,68,0,68
...
```

De kolommen Exported to Grid (Wh) en Imported from Grid (Wh) zijn optioneel. Ondersteunde datumformaten zijn:
- DD/MM/YYYY HH:MM
- YYYY-MM-DD HH:MM:SS
- MM/DD/YYYY HH:MM

## 🧩 Modules

De applicatie bestaat uit de volgende modules:

- **app.py**: Hoofdapplicatie met Streamlit UI
- **data_processor.py**: Verwerking van CSV-data
- **config_manager.py**: Beheer van gebruikersconfiguratie
- **storage_calculator.py**: Basisberekeningen voor energieopslag
- **boiler_module.py**: Berekeningen voor warmwaterboiler
- **battery_module.py**: Berekeningen voor accu-opslag
- **visualization.py**: Grafieken en visualisaties
- **utils.py**: Algemene hulpfuncties

## 📚 Werking van de applicatie

1. **Data Upload**: Upload uw CSV-bestand met energiegegevens
2. **Configuratie**: Pas de economische en technische parameters aan
3. **Warmwaterboiler Analyse**: Bereken de gasbesparing door overproductie te gebruiken voor waterverwarming
4. **Accu Analyse**: Bereken de kostenbesparing door overproductie op te slaan in een accu
5. **Visualisatie**: Bekijk grafieken en vergelijk de opties

## 🛠️ Technische details

De applicatie is gebouwd met:
- **Streamlit**: Voor de web-interface
- **Pandas**: Voor dataverwerking
- **Plotly**: Voor interactieve visualisaties
- **NumPy**: Voor numerieke berekeningen

## 📊 Voorbeeldgebruik

De repository bevat een voorbeeldbestand (examples/sample_energy_data.csv) dat kan worden gebruikt om de applicatie te testen.

## 📜 Licentie

Dit project is gelicenseerd onder de MIT License - zie het LICENSE bestand voor details.

## 👥 Bijdragen

Bijdragen aan de ontwikkeling zijn welkom! Open een issue of stuur een pull request.
