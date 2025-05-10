import reflex as rx
"""
Programa para calcular el sueldo neto en la República Dominicana,
considerando descuentos de seguridad social, retención de ISR y bonificación por antigüedad.
"""

# PORCENTAJE_TSS: Porcentaje de descuento por Seguridad Social (5.91%)
PORCENTAJE_TSS = 0.0591

# --- Escala Anual de Impuesto Sobre la Renta (ISR) en RD (Fuente: DGII) ---
ESCALA_ISR = [
    (416220.00, 0.00),     # Hasta RD$416,220.00: Exento
    (624329.00, 0.15),     # Desde RD$416,220.01 hasta RD$624,329.00: 15% del excedente
    (867123.00, 0.20, 31216.00),   # Desde RD$624,329.01 hasta RD$867,123.00: RD$31,216 más 20% del excedente
    (float('inf'), 0.25, 79776.00),   # Desde RD$867,123.01 en adelante: RD$79,776 más RD$79,776 más 25% del excedente
]

def calcular_isr_anual(salario_anual_bruto: float) -> float:
    """
    Calcula el Impuesto Sobre la Renta (ISR) anual según la escala en RD.
    """
    for limite, tasa, *cuota_fija in ESCALA_ISR:
        if salario_anual_bruto <= limite:
            if tasa == 0:
                return 0.0
            elif cuota_fija:
                limite_anterior = ESCALA_ISR[ESCALA_ISR.index((limite, tasa, *cuota_fija)) - 1][0] if ESCALA_ISR.index((limite, tasa, *cuota_fija)) > 0 else 0
                excedente = salario_anual_bruto - limite_anterior
                return cuota_fija[0] + (excedente * tasa)
            else:
                limite_anterior = ESCALA_ISR[ESCALA_ISR.index((limite, tasa)) - 1][0] if ESCALA_ISR.index((limite, tasa)) > 0 else 0
                excedente = salario_anual_bruto - limite_anterior
                return excedente * tasa
    return 0.0

class State(rx.State):
    sueldo_bruto: float = 0.0
    TiempoEmpresa: str = ""
    desea_bonificacion: bool = False
    descuento_tss: float = 0.0
    isr_Mensual: float = 0.0
    isr_anual: float = 0.0
    bonificacion: float = 0.0
    sueldo_neto: float = 0.0

    porcentaje_tss: float = PORCENTAJE_TSS
    escala_isr: list[tuple[float, float, float | None]] = ESCALA_ISR

    def set_sueldo_bruto(self, value: str):
        try:
            self.sueldo_bruto = float(value)
        except ValueError:
            self.sueldo_bruto = 0.0
        self.calcular_sueldo_neto() # Recalcular al cambiar el sueldo bruto

    def set_TiempoEmpresa(self, value: str):
        self.TiempoEmpresa = value
        self.calcular_sueldo_neto() 

    def set_desea_bonificacion(self, value: bool):
        self.desea_bonificacion = value
        self.calcular_sueldo_neto() 

    def calcular_isr_mensual(self, salario_anual_bruto: float) -> float:
        """Calcula el ISR anual y lo divide por 12 para obtener el valor mensual."""
        self.isr_anual = calcular_isr_anual(salario_anual_bruto)
        return self.isr_anual / 12 if self.isr_anual is not None else 0.0

    def calcular_bonificacion(self):
        if self.desea_bonificacion:
            if self.sueldo_bruto >= 0:
                if self.TiempoEmpresa == "Menos de 3 años":
                    self.bonificacion = self.sueldo_bruto / 23.83 * 45
                elif self.TiempoEmpresa == "3 años o más":
                    self.bonificacion = self.sueldo_bruto / 23.83 * 60
                else:
                    self.bonificacion = 0.0
            else:
                self.bonificacion = 0.0
        else:
            self.bonificacion = 0.0

    def calcular_sueldo_neto(self):
        if self.sueldo_bruto >= 0:
            salario_anual_bruto = self.sueldo_bruto * 12
            self.descuento_tss = self.sueldo_bruto * self.porcentaje_tss
            self.isr_Mensual = self.calcular_isr_mensual(salario_anual_bruto)
            self.calcular_bonificacion()
            self.sueldo_neto = (
                self.sueldo_bruto
                - self.descuento_tss
                - self.isr_Mensual
                + self.bonificacion
            )
        else:
            self.descuento_tss = 0.0
            self.isr_Mensual = 0.0
            self.isr_anual = 0.0
            self.bonificacion = 0.0
            self.sueldo_neto = 0.0

def index():
    return rx.vstack(
    
        rx.heading("Calculadora de Sueldo Neto (RD 2025)"),
        rx.input(
            placeholder="Sueldo Bruto Mensual",
            type="number",
            on_change=State.set_sueldo_bruto,
        ),
        rx.text("Seleccione cuanto tiempo lleva en la empresa:"),
        rx.select(
            ["Menos de 3 años", "3 años o más"],
            on_change=State.set_TiempoEmpresa,
        ),
        rx.checkbox(
            "¿Desea aplicar bonificación?",
            on_change=State.set_desea_bonificacion,
        ),
        rx.divider(),
        rx.text(f"Sueldo Bruto Mensual: RD$ {State.sueldo_bruto:,.2f}"),
        rx.text(
            f"Descuento TSS ({State.porcentaje_tss * 100:.2f}%): RD$ {State.descuento_tss:,.2f}"
        ),
        rx.text(f"Retención ISR (mensual): RD$ {State.isr_Mensual:,.2f}"),
        rx.text(f"ISR Anual: RD$ {State.isr_anual:,.2f}"),
        rx.text(f"Bonificación: RD$ {State.bonificacion:,.2f}"),
        rx.heading(f"Sueldo Neto Mensual: RD$ {State.sueldo_neto:,.2f}", size={"lg": "4"}), 
    )

app = rx.App()
app.add_page(index)