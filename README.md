
# Rup-IA: Reto de los 7500 goles

## Cómo ejecutar
1) Asegurate de tener en la misma carpeta:
   - `interactive_assignment.py` (con la clase `SequentialAssigner`)
   - `hungaro.py` (con la función `resolver_asignacion_optima`)
   - `goles_250812.csv`
   - `policy_premier.npy`, `policy_laliga.npy`, `policy_seriea.npy`, `policy_bundesliga.npy`, `policy_ligue1.npy`, `policy_eredivisie.npy`

2) Instalar dependencias (idealmente en un virtualenv):
```bash
pip install -r requirements.txt
```

3) Ejecutar la app:
```bash
streamlit run app.py
```

4) En el navegador, elegí la liga con BONUS y empezá a jugar.
