
import streamlit as st
import numpy as np
import pandas as pd
from difflib import get_close_matches
from pathlib import Path


try:
    from interactive_assignment import SequentialAssigner
except Exception as e:
    st.error("No pude importar 'interactive_assignment.SequentialAssigner'. Asegurate de que el archivo interactive_assignment.py esté en la misma carpeta.")
    st.stop()

ALLOWED_BONUS = ["Premier", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "Eredivisie"]

def load_goles(csv_file_or_path):
    if csv_file_or_path is None:
        raise ValueError("Falta el CSV de goles.")
    df = pd.read_csv(csv_file_or_path)
    jugadores = df.iloc[:, 0].astype(str).values
    ligas = df.columns[1:].tolist()
    G = df.iloc[:, 1:].to_numpy(dtype=np.float32)
    name_to_idx = {name: i for i, name in enumerate(jugadores)}
    league_to_idx = {nm: i for i, nm in enumerate(ligas)}
    return df, jugadores, ligas, G, name_to_idx, league_to_idx

def init_episode_state(ligas, G, name_to_idx, league_to_idx, bonus_name, policy_by_bonus):
    # Construir pesos base y aplicar BONUS x3 en la columna correspondiente
    base_M = np.array([5, 1, 1, 1, 1, 1, 1, 4, 3, 1, 2, 10, 40, 80, 250, 600], dtype=np.float32)
    if bonus_name not in league_to_idx:
        st.error(f"No encuentro la columna '{bonus_name}' en el CSV. Revisá los encabezados.")
        st.stop()
    bonus_col_idx = league_to_idx[bonus_name]
    if not (1 <= bonus_col_idx <= 6):
        st.error("El bonus ×3 solo se admite para {Premier, La Liga, Serie A, Bundesliga, Ligue 1, Eredivisie}.")
        st.stop()

    M = base_M.copy()
    M[bonus_col_idx] = 3.0
    GM = (G * M[None, :]).astype(np.float32)

    # Cargar policy asociada a la liga de bonus
    policy_path = policy_by_bonus.get(bonus_name)
    if policy_path is None or not Path(policy_path).exists():
        st.error(f"No encuentro el archivo de política para {bonus_name}. Esperaba: {policy_path}")
        st.stop()

    assigner = SequentialAssigner.from_policy(str(policy_path))

    # Estado inicial
    st.session_state["assigner"] = assigner
    st.session_state["usados"] = set()
    st.session_state["total"] = 0.0
    st.session_state["picks"] = []  # lista de dicts {jugador, liga, valor}
    st.session_state["GM"] = GM
    st.session_state["G"] = G
    st.session_state["ligas"] = ligas
    st.session_state["name_to_idx"] = name_to_idx
    st.session_state["jugadores"] = list(name_to_idx.keys())

def main():
    st.set_page_config(page_title="Rup-IA", page_icon="⚽", layout="centered")
    st.title("🤖⚽ Rup-IA")
    st.caption("Simulador de estrategia óptima para el reto de los 7500 goles.")

    # === Panel de configuración ===
    with st.expander("❓ ¿Qué liga multiplica hoy?", expanded=True):
        # CSV: se puede subir o usar ruta local
        csv_path = "goles_250812.csv"

        bonus_name = st.selectbox("Liga con BONUS ×3", ALLOWED_BONUS, index=0)

        # Mapeo liga->archivo de política (ajustá nombres según tus archivos reales)
        policy_by_bonus = {
            "Premier": "policy_premier.npy",
            "La Liga": "policy_laliga.npy",
            "Serie A": "policy_seriea.npy",
            "Bundesliga": "policy_bundesliga.npy",
            "Ligue 1": "policy_ligue1.npy",
            "Eredivisie": "policy_eredivisie.npy",
        }

        start_btn = st.button("🚀 Iniciar reto", type="primary")

    # Cargar dataset si se presionó "Iniciar"
    if start_btn:
        try:
            df, jugadores, ligas, G, name_to_idx, league_to_idx = load_goles(csv_path)
        except Exception as e:
            st.error(f"Error al leer el CSV: {e}")
            st.stop()

        init_episode_state(ligas, G, name_to_idx, league_to_idx, bonus_name, policy_by_bonus)
        bonus_name_display = "La " + bonus_name if bonus_name != "La Liga" else bonus_name
        st.success(f"¡{bonus_name_display}! ¡Vamos!")

    # Si no hay episodio en curso, nada más que hacer
    if "assigner" not in st.session_state:
        st.stop()

    assigner = st.session_state["assigner"]
    G = st.session_state["G"]
    GM = st.session_state["GM"]
    ligas = st.session_state["ligas"]
    name_to_idx = st.session_state["name_to_idx"]
    jugadores = st.session_state["jugadores"]

    st.divider()
    st.subheader("👤 Ingreso de jugadores")

    # Autocompletar por nombre
    no_usados = [j for j in jugadores if name_to_idx[j] not in st.session_state["usados"]]
    col1, col2 = st.columns([2,1], vertical_alignment="bottom")
    with col1:
        jugador_sel = st.selectbox("Elegí un jugador:", no_usados, index=0 if no_usados else None, key="sel_jugador")
    with col2:
        confirmar = st.button("✅ Asignar automáticamente")

    if confirmar and no_usados:
        pid = name_to_idx[jugador_sel]
        if pid in st.session_state["usados"]:
            st.warning("Ese jugador ya fue elegido. Probá con otro.")
        else:
            best_slot = assigner.assign_next(pid)
            liga_asignada = ligas[best_slot]
            valor = float(GM[pid, best_slot])
            st.session_state["total"] += valor
            st.session_state["usados"].add(pid)
            st.session_state["picks"].append({"Jugador": jugador_sel, "Liga": liga_asignada, "Valor": int(valor)})

            st.success(f"✅ {jugador_sel} → {liga_asignada} | Puntos: {int(valor)} | Total: {int(st.session_state['total'])}")

    # Mostrar estado
    st.divider()
    st.subheader("📊 Estado del juego")
    st.metric("Puntaje acumulado", int(st.session_state["total"]))
    libres = assigner.categories_left()
    ligas_libres = [ligas[i] if ligas[i].upper() != bonus_name.upper() else ligas[i] + " (x3)" for i in libres]
    st.caption(f"Categorías libres: {ligas_libres}")
    if st.session_state["picks"]:
        st.dataframe(pd.DataFrame(st.session_state["picks"]), use_container_width=True)

    # Finalización
    if assigner.is_finished():
        st.balloons()
        st.success(f"🏁 ¡Juego finalizado! Puntaje total: {int(st.session_state['total'])}")

    # Panel opcional: ranking de mejores próximos (Top-K heurístico)
    with st.expander("🧠 Sugerencias de próximos jugadores (según policy y estado actual)"):
        try:
            mask = assigner.mask
            candidates = []
            for name in no_usados[:5000]:
                t = name_to_idx[name]
                slot = int(assigner.policy[mask, t])
                val = float(GM[t, slot])
                candidates.append((name, ligas[slot], int(val)))
            top = sorted(candidates, key=lambda x: x[2], reverse=True)[:20]
            if top:
                df_top = pd.DataFrame(top, columns=["Jugador", "Liga sugerida", "Valor estimado"])
                st.dataframe(df_top, use_container_width=True)
            else:
                st.write("Sin candidatos (¿ya terminaste el juego?).")
        except Exception as e:
            st.info("No se pudieron calcular sugerencias. Detalle: " + str(e))

if __name__ == "__main__":
    main()
