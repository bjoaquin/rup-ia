# hungaro.py
import numpy as np
from scipy.optimize import linear_sum_assignment

def resolver_asignacion_optima(matriz):
    """
    Aplica el algoritmo húngaro para maximizar el puntaje total.

    Parámetro:
        matriz (np.ndarray): matriz de costos (jugadores × competencias)

    Retorna:
        int: puntaje máximo total
    """
    # Convertir a problema de minimización (porque el método minimiza)
    matriz_para_min = matriz.max() - matriz

    # Aplicar método húngaro
    fila_ind, col_ind = linear_sum_assignment(matriz_para_min)

    # Calcular puntaje total máximo
    puntaje_total = matriz[fila_ind, col_ind].sum()

    return puntaje_total
