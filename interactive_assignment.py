# interactive_assignment.py (versión corregida)
import numpy as np
from pathlib import Path
from typing import List, Optional

class SequentialAssigner:
    """
    Uso:
        assigner = SequentialAssigner.from_policy("policy.npy")
        # opcionalmente: assigner.set_slot_names([...])
        slot = assigner.assign_next(player_type=37)  # devuelve índice de categoría óptima
    """
    def __init__(self, policy: np.ndarray, slot_names: Optional[List[str]] = None):
        """
        policy: array de shape (2^m_slots, n_types).
                policy[mask, t] = mejor slot (0..m_slots-1) para un jugador de tipo t
                cuando las categorías libres están dadas por 'mask'.
        """
        if policy.ndim != 2:
            raise ValueError("policy debe ser 2D: (2^m_slots, n_types)")
        self.policy = policy.astype(np.int64, copy=False)

        self.M_masks, self.n_types = self.policy.shape
        m_slots = int(np.round(np.log2(self.M_masks)))
        if (1 << m_slots) != self.M_masks:
            raise ValueError("El primer eje de policy no es potencia de 2.")
        self.m_slots = m_slots

        self.full_mask = (1 << self.m_slots) - 1
        self.mask = self.full_mask  # estado actual (todas las categorías libres)
        self.slot_names = slot_names  # nombres humanos de categorías (opcional)

    @classmethod
    def from_policy(cls, policy_path: str, slot_names: Optional[List[str]] = None):
        policy = np.load(policy_path)
        return cls(policy, slot_names)

    def reset(self):
        """Restablece todas las categorías como libres."""
        self.mask = self.full_mask

    def categories_left(self) -> List[int]:
        """Lista de índices de categorías aún libres."""
        return [j for j in range(self.m_slots) if (self.mask >> j) & 1]

    def is_finished(self) -> bool:
        """True si ya se asignaron todas las categorías."""
        return self.mask == 0

    def assign_next(self, player_type: int):
        """
        Dado el tipo de jugador 'player_type' (0..n_types-1), devuelve la categoría óptima y actualiza el estado.
        """
        if self.mask == 0:
            raise RuntimeError("No quedan categorías disponibles.")

        if not (0 <= player_type < self.n_types):
            raise ValueError(f"player_type fuera de rango [0, {self.n_types-1}]")

        slot = int(self.policy[self.mask, player_type])

        # Validación defensiva: la categoría propuesta debe estar libre
        if ((self.mask >> slot) & 1) == 0:
            free_slots = self.categories_left()
            if not free_slots:
                raise RuntimeError("No quedan categorías disponibles (inconsistencia).")
            slot = free_slots[0]

        # Ocupar slot: apagar bit
        self.mask ^= (1 << slot)

        # Devolver nombre humano si está definido
        return self.slot_names[slot] if self.slot_names else slot

    def pretty_slot(self, idx: int) -> str:
        return self.slot_names[idx] if self.slot_names else str(idx)

if __name__ == "__main__":
    # Ejemplo de uso rápido:
    path = "policy_laliga.npy"   # o "policy.npy"
    slot_names = [f"Cat {j}" for j in range(16)]  # opcional (ajustá a tu m_slots si no es 16)
    assigner = SequentialAssigner.from_policy(path, slot_names)

    # Simular llegadas secuenciales de tipos de jugador (índices en 0..n_types-1, p.ej. 0..191)
    example_stream = [0, 3, 7, 7, 2, 11, 4, 5, 1, 6, 8, 9, 10, 12, 13, 14]
    for t in example_stream:
        best_slot = assigner.assign_next(t)
        print(f"Jugador tipo {t} → asignar a {best_slot} | libres: {assigner.categories_left()}")
