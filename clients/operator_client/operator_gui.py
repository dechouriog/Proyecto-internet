import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================
# VENTANA DE LOGIN
# =============================================================
class LoginWindow:
    def __init__(self, root, client, on_success):
        self.root = root
        self.client = client
        self.on_success = on_success

        self.root.title("Monitoreo Ambiental — Acceso")
        self.root.geometry("480x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#060f0a")
        self._center()

        self.C = {
            "bg": "#060f0a",
            "panel": "#0c1c10",
            "panel_2": "#0f2214",
            "border": "#1d4a28",
            "text": "#e8f5ea",
            "muted": "#7aab85",
            "green": "#22c55e",
            "green_soft": "#14532d",
            "green_bright": "#4ade80",
            "line": "#163a1e",
            "red": "#f87171",
        }
        self._build()

    def _center(self):
        self.root.update_idletasks()
        w, h = 480, 560
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        C = self.C
        outer = tk.Frame(self.root, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=40, pady=40)

        # Logo
        logo_box = tk.Frame(
            outer,
            bg="#0d2e14",
            width=80,
            height=80,
            highlightthickness=2,
            highlightbackground="#1d5e2a",
        )
        logo_box.pack()
        logo_box.pack_propagate(False)
        tk.Label(
            logo_box,
            text="🌿",
            font=("Segoe UI Emoji", 32),
            fg=C["green_bright"],
            bg="#0d2e14",
        ).pack(expand=True)

        tk.Label(
            outer,
            text="Centro de Monitoreo",
            font=("Segoe UI", 20, "bold"),
            fg=C["text"],
            bg=C["bg"],
        ).pack(pady=(14, 0))
        tk.Label(
            outer,
            text="Ambiental Urbano",
            font=("Segoe UI", 20, "bold"),
            fg=C["green_bright"],
            bg=C["bg"],
        ).pack()
        tk.Label(
            outer,
            text="Sistema de supervisión de calidad del aire",
            font=("Segoe UI", 10),
            fg=C["muted"],
            bg=C["bg"],
        ).pack(pady=(6, 24))

        # Card form
        card = tk.Frame(
            outer, bg=C["panel"], highlightthickness=1, highlightbackground=C["border"]
        )
        card.pack(fill="x")
        inner = tk.Frame(card, bg=C["panel"])
        inner.pack(fill="x", padx=28, pady=28)

        tk.Label(
            inner,
            text="INICIAR SESIÓN",
            font=("Segoe UI", 11, "bold"),
            fg=C["green_bright"],
            bg=C["panel"],
        ).pack(anchor="w", pady=(0, 16))

        tk.Label(
            inner,
            text="Usuario",
            font=("Segoe UI", 10, "bold"),
            fg=C["muted"],
            bg=C["panel"],
        ).pack(anchor="w")
        self.user_entry = tk.Entry(
            inner,
            font=("Segoe UI", 12),
            bg="#060f0a",
            fg=C["text"],
            insertbackground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=C["line"],
            highlightcolor=C["green_soft"],
        )
        self.user_entry.pack(fill="x", ipady=10, pady=(4, 14))

        tk.Label(
            inner,
            text="Contraseña",
            font=("Segoe UI", 10, "bold"),
            fg=C["muted"],
            bg=C["panel"],
        ).pack(anchor="w")
        self.pass_entry = tk.Entry(
            inner,
            font=("Segoe UI", 12),
            bg="#060f0a",
            fg=C["text"],
            insertbackground="white",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=C["line"],
            highlightcolor=C["green_soft"],
            show="*",
        )
        self.pass_entry.pack(fill="x", ipady=10, pady=(4, 18))

        self.error_var = tk.StringVar()
        tk.Label(
            inner,
            textvariable=self.error_var,
            font=("Segoe UI", 9),
            fg=C["red"],
            bg=C["panel"],
        ).pack(anchor="w", pady=(0, 8))

        self.login_btn = tk.Button(
            inner,
            text="Ingresar al sistema",
            command=self._do_login,
            bg=C["green_soft"],
            fg="white",
            activebackground="#1a6b38",
            activeforeground="white",
            relief="flat",
            bd=0,
            font=("Segoe UI", 11, "bold"),
            pady=12,
            cursor="hand2",
        )
        self.login_btn.pack(fill="x")

        self.root.bind("<Return>", lambda e: self._do_login())
        self.user_entry.focus()

        tk.Label(
            outer,
            text="v1.0  •  MAU Sistema Distribuido",
            font=("Segoe UI", 9),
            fg=C["muted"],
            bg=C["bg"],
        ).pack(pady=(16, 0))

    def _do_login(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()
        if not u or not p:
            self.error_var.set("⚠  Ingresa usuario y contraseña")
            return
        self.error_var.set("")
        self.login_btn.configure(text="Verificando...", state="disabled")
        self.root.configure(cursor="watch")

        import threading

        def _work():
            try:
                self.client.login(u, p)
                ok = self.client.user_id is not None
            except Exception:
                ok = False
            self.root.after(0, lambda: self._login_done(ok, u))

        threading.Thread(target=_work, daemon=True).start()

    def _login_done(self, ok, username):
        self.root.configure(cursor="")
        self.login_btn.configure(text="Ingresar al sistema", state="normal")
        if ok:
            self.root.destroy()
            self.on_success(username)
        else:
            self.error_var.set("✖  Usuario o contraseña incorrectos")
            self.pass_entry.delete(0, "end")
            self.pass_entry.focus()


# =============================================================
# DASHBOARD PRINCIPAL
# =============================================================
class OperatorGUI:
    def __init__(self, root, client, username="operador"):
        self.root = root
        self.client = client
        self.username = username

        self.root.title("Centro de Monitoreo Ambiental Urbano")
        self.root.geometry("1720x980")
        self.root.minsize(1500, 860)
        self.root.configure(bg="#060f0a")

        self.C = {
            "bg": "#060f0a",
            "panel": "#0c1c10",
            "panel_2": "#0f2214",
            "panel_3": "#122818",
            "border": "#1d4a28",
            "text": "#e8f5ea",
            "muted": "#7aab85",
            "green": "#22c55e",
            "green_soft": "#14532d",
            "green_bright": "#4ade80",
            "teal": "#2dd4bf",
            "yellow": "#facc15",
            "red": "#f87171",
            "blue": "#60a5fa",
            "line": "#163a1e",
        }

        self.status_var = tk.StringVar(value="Conectado")
        self.last_update_var = tk.StringVar(value="--:--:--")
        self.alert_count_var = tk.StringVar(value="0")
        self.sensor_count_var = tk.StringVar(value="0")
        self.clock_var = tk.StringVar(value="--:--:--")
        self.auto_refresh_var = tk.StringVar(value="OFF")
        self.system_state_var = tk.StringVar(value="Cargando...")
        self.critical_count_var = tk.StringVar(value="0")
        self.medium_count_var = tk.StringVar(value="0")
        self.sim_state_var = tk.StringVar(value="Activo")

        self.sensors_tree = None
        self.alerts_tree = None
        self.auto_refresh_enabled = False
        self.refresh_job = None
        self._refreshing = False  # Evita ciclos solapados de auto-refresh
        self.recent_events = []
        self._ar_btn = None

        self._configure_styles()
        self._build_ui()
        self._update_clock()
        self._push_event("Sistema", f"Sesión iniciada como {self.username}", "success")
        self.refresh_all(initial=True)

    # --- Estilos ---
    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass
        style.configure(
            "Treeview",
            background=self.C["panel"],
            fieldbackground=self.C["panel"],
            foreground=self.C["text"],
            rowheight=34,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", self.C["green_soft"])])
        style.configure(
            "Treeview.Heading",
            background=self.C["panel_3"],
            foreground=self.C["green_bright"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )

    # --- Layout ---
    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main = tk.Frame(self.root, bg=self.C["bg"])
        self.main.grid(row=0, column=0, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_stat_cards()
        self._build_body()

    # --- Header ---
    def _build_header(self):
        hdr = tk.Frame(self.main, bg=self.C["bg"])
        hdr.grid(row=0, column=0, sticky="ew", padx=22, pady=(14, 6))
        hdr.grid_columnconfigure(0, weight=1)

        left = tk.Frame(hdr, bg=self.C["bg"])
        left.grid(row=0, column=0, sticky="w")
        tk.Label(
            left,
            text="Centro de Monitoreo Ambiental Urbano",
            font=("Segoe UI", 26, "bold"),
            fg=self.C["text"],
            bg=self.C["bg"],
        ).pack(anchor="w")
        tk.Label(
            left,
            text=f"Panel de Operador  •  {self.username}  •  Supervisión de calidad del aire",
            font=("Segoe UI", 12),
            fg=self.C["muted"],
            bg=self.C["bg"],
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(hdr, bg=self.C["bg"])
        right.grid(row=0, column=1, sticky="e")

        chip = tk.Frame(
            right, bg="#0c2a12", highlightthickness=1, highlightbackground="#1d5e2a"
        )
        chip.grid(row=0, column=0, padx=(0, 12), pady=2)
        tk.Label(
            chip,
            text="●",
            fg=self.C["green"],
            bg="#0c2a12",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(12, 6), pady=10)
        tk.Label(
            chip,
            textvariable=self.status_var,
            fg="#a7f3c0",
            bg="#0c2a12",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 12))

        tk.Button(
            right,
            text="⏻  Cerrar sesión",
            command=self._on_logout,
            bg="#2e0d0d",
            fg=self.C["red"],
            activebackground="#3e1010",
            activeforeground=self.C["red"],
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=8,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground="#6e1c1c",
        ).grid(row=0, column=1, padx=(0, 16))

        tk.Frame(right, bg=self.C["line"], width=1, height=52).grid(
            row=0, column=2, padx=(0, 16)
        )

        clk = tk.Frame(right, bg=self.C["bg"])
        clk.grid(row=0, column=3, padx=(0, 16))
        tk.Label(
            clk,
            text="Hora del sistema",
            fg=self.C["muted"],
            bg=self.C["bg"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            clk,
            textvariable=self.clock_var,
            fg=self.C["green_bright"],
            bg=self.C["bg"],
            font=("Consolas", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            clk,
            text=datetime.now().strftime("%d de %B de %Y"),
            fg=self.C["muted"],
            bg=self.C["bg"],
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        ar = tk.Frame(right, bg=self.C["bg"])
        ar.grid(row=0, column=4)
        tk.Label(
            ar,
            text="Auto refresh",
            fg=self.C["muted"],
            bg=self.C["bg"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        ar_row = tk.Frame(ar, bg=self.C["bg"])
        ar_row.pack(anchor="w", pady=(4, 0))
        tk.Label(
            ar_row,
            textvariable=self.auto_refresh_var,
            fg=self.C["text"],
            bg=self.C["bg"],
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left", padx=(0, 8))
        self._ar_btn = tk.Button(
            ar_row,
            text=" OFF ",
            command=self._toggle_ar,
            width=5,
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        self._ar_btn.pack(side="left")
        self._refresh_ar_button()

    # --- Stat cards ---
    def _build_stat_cards(self):
        wrap = tk.Frame(self.main, bg=self.C["bg"])
        wrap.grid(row=1, column=0, sticky="ew", padx=22, pady=(6, 12))
        for i in range(5):
            wrap.grid_columnconfigure(i, weight=1)

        def card(col):
            c = tk.Frame(
                wrap,
                bg=self.C["panel"],
                highlightthickness=1,
                highlightbackground=self.C["border"],
            )
            c.grid(row=0, column=col, sticky="nsew", padx=7)
            return c

        def icon(parent, emoji, fill, outline):
            cv = tk.Canvas(
                parent,
                width=78,
                height=78,
                bg=self.C["panel"],
                bd=0,
                highlightthickness=0,
            )
            cv.pack()
            cv.create_oval(5, 5, 73, 73, fill=fill, outline=outline)
            cv.create_text(39, 39, text=emoji, font=("Segoe UI Emoji", 26))
            return cv

        for col, (em, fi, ou, title, var, fg, sub) in enumerate(
            [
                (
                    "🛡",
                    "#0d2e14",
                    "#1a5e2a",
                    "ESTADO GENERAL",
                    self.system_state_var,
                    self.C["green"],
                    "Sistema activo",
                ),
                (
                    "📡",
                    "#0c2241",
                    "#1a4070",
                    "SENSORES ACTIVOS",
                    self.sensor_count_var,
                    self.C["text"],
                    "nodos conectados",
                ),
                (
                    "🚨",
                    "#3a0d0d",
                    "#6e1c1c",
                    "ALERTAS CRITICAS",
                    self.critical_count_var,
                    self.C["red"],
                    "requieren atencion",
                ),
                (
                    "⚠",
                    "#3a2d00",
                    "#786010",
                    "ALERTAS MEDIAS",
                    self.medium_count_var,
                    self.C["yellow"],
                    "en seguimiento",
                ),
                (
                    "🕘",
                    "#1a1a3e",
                    "#2e2e70",
                    "ULTIMA ACTUALIZACION",
                    self.last_update_var,
                    self.C["text"],
                    "ultima sincronizacion",
                ),
            ]
        ):
            c = card(col)
            lft = tk.Frame(c, bg=self.C["panel"])
            lft.pack(side="left", padx=16, pady=16)
            icon(lft, em, fi, ou)
            rgt = tk.Frame(c, bg=self.C["panel"])
            rgt.pack(side="left", fill="both", expand=True, padx=(0, 16))
            tk.Label(
                rgt,
                text=title,
                fg=self.C["muted"],
                bg=self.C["panel"],
                font=("Segoe UI", 9, "bold"),
            ).pack(anchor="w", pady=(16, 2))
            tk.Label(
                rgt,
                textvariable=var,
                fg=fg,
                bg=self.C["panel"],
                font=("Segoe UI", 22 if col in (0, 4) else 28, "bold"),
            ).pack(anchor="w")
            tk.Label(
                rgt,
                text=sub,
                fg=self.C["muted"],
                bg=self.C["panel"],
                font=("Segoe UI", 10),
            ).pack(anchor="w")

    # --- Body ---
    def _build_body(self):
        body = tk.Frame(self.main, bg=self.C["bg"])
        body.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 16))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        # Barra de controles — fila 0, span 2 cols
        ctrl_bar = tk.Frame(
            body,
            bg=self.C["panel"],
            highlightthickness=1,
            highlightbackground=self.C["border"],
        )
        ctrl_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ctrl_bar.grid_columnconfigure(0, weight=1)
        ctrl_bar.grid_columnconfigure(2, weight=1)

        sec1 = tk.Frame(ctrl_bar, bg=self.C["panel"])
        sec1.grid(row=0, column=0, sticky="nsew", padx=24, pady=16)
        tk.Label(
            sec1,
            text="ACCIONES RÁPIDAS",
            fg=self.C["green_bright"],
            bg=self.C["panel"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        br = tk.Frame(sec1, bg=self.C["panel"])
        br.pack(anchor="w")
        self._btn_small(br, "↻  Actualizar todo", self.refresh_all).pack(
            side="left", padx=(0, 8)
        )
        self._btn_small(br, "⊙  Estado sistema", self._on_status).pack(
            side="left", padx=(0, 8)
        )
        self._btn_small(br, "✓  Validar sesión", self._on_validate).pack(side="left")

        tk.Frame(ctrl_bar, bg=self.C["line"], width=1).grid(
            row=0, column=1, sticky="ns", pady=10
        )

        sec2 = tk.Frame(ctrl_bar, bg=self.C["panel"])
        sec2.grid(row=0, column=2, sticky="nsew", padx=24, pady=16)
        tk.Label(
            sec2,
            text="MONITOREO Y SIMULACIÓN",
            fg=self.C["green_bright"],
            bg=self.C["panel"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        row_ar = tk.Frame(sec2, bg=self.C["panel"])
        row_ar.pack(anchor="w", pady=(0, 8))
        tk.Label(
            row_ar,
            text="Auto refresh (5s):",
            bg=self.C["panel"],
            fg=self.C["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 8))
        self._ar_btn = tk.Button(
            row_ar,
            text=" OFF ",
            command=self._toggle_ar,
            width=5,
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        self._ar_btn.pack(side="left")
        self._refresh_ar_button()

        row_sim = tk.Frame(sec2, bg=self.C["panel"])
        row_sim.pack(anchor="w")
        tk.Label(
            row_sim,
            text="Simulación:",
            bg=self.C["panel"],
            fg=self.C["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 8))
        tk.Label(
            row_sim,
            textvariable=self.sim_state_var,
            bg=self.C["panel"],
            fg=self.C["green"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 14))
        self._btn_small(row_sim, "⏸ Pausar", self._on_pause).pack(
            side="left", padx=(0, 6)
        )
        self._btn_small(row_sim, "▶ Reanudar", self._on_resume).pack(side="left")

        # Panel alertas — fila 1 col 0
        self._build_panel_alertas(body)

        # Panel sensores — fila 1 col 1
        self._build_panel_sensores(body)

    def _build_panel_alertas(self, parent):
        panel = tk.Frame(
            parent,
            bg=self.C["panel"],
            highlightthickness=1,
            highlightbackground=self.C["border"],
        )
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        th = tk.Frame(panel, bg=self.C["panel"])
        th.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        lft = tk.Frame(th, bg=self.C["panel"])
        lft.pack(side="left")
        tk.Label(
            lft,
            text="🚨",
            bg=self.C["panel"],
            fg=self.C["red"],
            font=("Segoe UI Emoji", 16),
        ).pack(side="left")
        tk.Label(
            lft,
            text="ALERTAS AMBIENTALES ACTIVAS",
            bg=self.C["panel"],
            fg=self.C["text"],
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=(8, 0))
        rgt = tk.Frame(th, bg=self.C["panel"])
        rgt.pack(side="right")
        self._btn_outline(
            rgt, "Actualizar", self._update_alerts, self.C["teal"], width=11
        ).pack()

        tf = tk.Frame(panel, bg=self.C["panel"])
        tf.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 6))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("id", "sensor", "tipo", "nivel", "mensaje", "hora")
        widths = [55, 100, 110, 90, 420, 170]
        heads = ["ID", "Sensor", "Tipo", "Nivel", "Mensaje", "Hora"]
        self.alerts_tree = ttk.Treeview(tf, columns=cols, show="headings", height=12)
        for c, w, h in zip(cols, widths, heads):
            self.alerts_tree.heading(c, text=h)
            self.alerts_tree.column(
                c, width=w, anchor="center" if c != "mensaje" else "w"
            )
        ys = ttk.Scrollbar(tf, orient="vertical", command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=ys.set)
        self.alerts_tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")

        ctrl = tk.Frame(panel, bg=self.C["panel"])
        ctrl.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        self._btn_outline(
            ctrl, "ACK alerta", self._on_ack, self.C["yellow"], width=12
        ).pack(side="left", padx=(0, 8))
        self._btn_outline(
            ctrl, "Limpiar alertas", self._on_clear, self.C["red"], width=14
        ).pack(side="left")

    def _build_panel_sensores(self, parent):
        panel = tk.Frame(
            parent,
            bg=self.C["panel"],
            highlightthickness=1,
            highlightbackground=self.C["border"],
        )
        panel.grid(row=1, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        th = tk.Frame(panel, bg=self.C["panel"])
        th.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        lft = tk.Frame(th, bg=self.C["panel"])
        lft.pack(side="left")
        tk.Label(
            lft,
            text="📡",
            bg=self.C["panel"],
            fg=self.C["teal"],
            font=("Segoe UI Emoji", 16),
        ).pack(side="left")
        tk.Label(
            lft,
            text="SENSORES REGISTRADOS",
            bg=self.C["panel"],
            fg=self.C["text"],
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=(8, 0))
        rgt = tk.Frame(th, bg=self.C["panel"])
        rgt.pack(side="right")
        self._btn_outline(
            rgt, "Actualizar", self._update_sensors, self.C["teal"], width=11
        ).pack()

        tf = tk.Frame(panel, bg=self.C["panel"])
        tf.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 6))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        cols = ("id", "tipo", "zona", "estado", "ultima")
        widths = [90, 120, 200, 110, 210]
        heads = ["ID", "Tipo", "Zona", "Estado", "Ultima lectura"]
        self.sensors_tree = ttk.Treeview(tf, columns=cols, show="headings", height=12)
        for c, w, h in zip(cols, widths, heads):
            self.sensors_tree.heading(c, text=h)
            self.sensors_tree.column(c, width=w, anchor="center")
        ys = ttk.Scrollbar(tf, orient="vertical", command=self.sensors_tree.yview)
        self.sensors_tree.configure(yscrollcommand=ys.set)
        self.sensors_tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")

        ctrl = tk.Frame(panel, bg=self.C["panel"])
        ctrl.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        self._btn_outline(
            ctrl, "Ver lecturas", self._show_readings, self.C["blue"], width=13
        ).pack(side="left")

    # --- Botones ---
    def _btn_outline(self, parent, text, cmd, color, width=13):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=self.C["panel"],
            fg=color,
            activebackground=self.C["panel_2"],
            activeforeground=color,
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=7,
            width=width,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=color,
            highlightcolor=color,
        )

    def _btn_small(self, parent, text, cmd):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=self.C["panel_3"],
            fg=self.C["text"],
            activebackground=self.C["panel_3"],
            activeforeground=self.C["text"],
            relief="flat",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=9,
            pady=9,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=self.C["line"],
        )

    def _refresh_ar_button(self):
        if not self._ar_btn:
            return
        txt = " ON " if self.auto_refresh_enabled else " OFF "
        bg = self.C["green_soft"] if self.auto_refresh_enabled else "#2a3a2e"
        self._ar_btn.configure(
            text=txt, bg=bg, fg="white", activebackground=bg, activeforeground="white"
        )

    # --- Helpers ---
    def _looks_sensor(self, p):
        if len(p) < 4:
            return False
        valid = bool(re.match(r"^[A-Z0-9][A-Z0-9\-]+$", p[0].strip()))
        return (
            valid
            and p[3].strip().lower() in {"activo", "active", "inactive", "inactivo"}
            and p[2].strip().lower() not in {"high", "medium", "low"}
        )

    def _looks_alert(self, p):
        if len(p) < 6:
            return False
        return p[0].strip().isdigit() and p[3].strip().lower() in {
            "high",
            "medium",
            "low",
        }

    def _format_reading(self, tipo, response):
        units = {
            "co2": "ppm",
            "ruido": "dB",
            "temperatura": "C",
            "pm25": "ug/m3",
            "humedad": "%",
            "uv": "idx",
        }
        unit = units.get(tipo.lower(), "")
        for line in response.splitlines():
            line = line.strip()
            if (
                not line
                or line.upper().startswith("READING")
                or line.startswith("sin_")
            ):
                continue
            if "|" not in line:
                continue
            p = [x.strip() for x in line.split("|")]
            for idx in [3, 2, 1]:
                if idx >= len(p):
                    continue
                try:
                    val = round(float(p[idx]), 2)
                    ts = p[idx + 1].strip() if idx + 1 < len(p) else ""
                    hora = ts.split(" ")[-1][:5] if ts else ""
                    return f"{val} {unit}  ({hora})" if hora else f"{val} {unit}"
                except (ValueError, IndexError):
                    continue
        return "--"

    def _parse_status(self, resp):
        st = {
            "overall": "Operativo",
            "simulation": "RUNNING",
            "active_sensors": "0",
            "active_alerts": "0",
        }
        for line in resp.splitlines():
            if "|" not in line:
                continue
            k, _, v = line.partition("|")
            if k.strip() in st:
                st[k.strip()] = v.strip()
        return st

    def _push_event(self, src, detail, level="info"):
        pass  # eventos eliminados del UI — solo log interno

    # --- Async ---
    def _run_async(self, fn, *args):
        import threading

        threading.Thread(target=fn, args=args, daemon=True).start()

    def _ui(self, fn, *args):
        self.root.after(0, fn, *args)

    def _set_busy(self, busy):
        self.root.configure(cursor="watch" if busy else "")

    def _update_clock(self):
        self.clock_var.set(datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._update_clock)

    # --- Acciones ---
    def _on_logout(self):
        if not messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar la sesión?"):
            return
        self._set_busy(True)

        def _work():
            try:
                self.client.logout()
            except:
                pass
            self._ui(self._restart_to_login)

        self._run_async(_work)

    def _restart_to_login(self):
        if self.refresh_job:
            try:
                self.root.after_cancel(self.refresh_job)
            except:
                pass
        self.root.destroy()
        _launch_login()

    def _on_validate(self):
        self._set_busy(True)

        def _work():
            try:
                resp = self.client.validate()
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showinfo("Validación", resp or "Sesión válida"),
                    )
                )
            except Exception as e:
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showwarning("Validación", str(e)),
                    )
                )

        self._run_async(_work)

    def _on_status(self):
        self._set_busy(True)

        def _work():
            try:
                resp = self.client.get_system_status()
                st = self._parse_status(resp)

                def _done():
                    self._set_busy(False)
                    self.system_state_var.set(
                        "En alerta" if st["overall"].upper() == "ALERT" else "Normal"
                    )
                    self.sim_state_var.set(
                        "Pausado" if st["simulation"].upper() == "PAUSED" else "Activo"
                    )
                    self.sensor_count_var.set(st["active_sensors"])
                    self.alert_count_var.set(st["active_alerts"])
                    messagebox.showinfo("Estado del sistema", resp or "Sin datos")

                self._ui(_done)
            except Exception as e:
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showerror("Estado", str(e)),
                    )
                )

        self._run_async(_work)

    def _update_sensors(self):
        # Versión async — lanza hilo propio (solo usar cuando NO viene de refresh_all)
        if self._refreshing:
            return
        self._refreshing = True

        def _wrap():
            try:
                self._update_sensors_sync()
            finally:
                self._refreshing = False

        self._run_async(_wrap)

    def _update_sensors_sync(self):
        # Versión síncrona — se ejecuta en el hilo del llamador (segura para secuenciar)
        import socket as _s, time as _t

        self._ui(lambda: self._set_busy(True))
        try:
            resp = self.client.get_sensors()
            info = []
            for line in resp.splitlines():
                line = line.strip()
                if not line or "|" not in line:
                    continue
                p = [x.strip() for x in line.split("|")]
                if self._looks_sensor(p):
                    info.append(p)

            rows = []
            for p in info:
                sid, tipo, zona, estado = p[:4]
                last = "--"
                try:
                    sock = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                    sock.settimeout(3)
                    sock.connect((self.client.host, self.client.port))
                    sock.sendall(f"GET_READINGS {sid}\n".encode())
                    raw = b""
                    _t.sleep(0.1)
                    sock.settimeout(1)
                    try:
                        while True:
                            chunk = sock.recv(4096)
                            if not chunk:
                                break
                            raw += chunk
                    except:
                        pass
                    sock.close()
                    last = self._format_reading(tipo, raw.decode(errors="replace"))
                except:
                    pass
                rows.append(
                    (
                        sid,
                        tipo,
                        zona,
                        (
                            "🟢 Activo"
                            if estado.lower() in {"activo", "active"}
                            else estado
                        ),
                        last,
                    )
                )

            snapshot = list(rows)  # Copia inmutable para el closure

            def _done():
                self._set_busy(False)
                for item in self.sensors_tree.get_children():
                    self.sensors_tree.delete(item)
                for row in snapshot:
                    self.sensors_tree.insert("", "end", values=row)
                self.sensor_count_var.set(str(len(snapshot)))
                self.last_update_var.set(datetime.now().strftime("%H:%M:%S"))

            self._ui(_done)
        except Exception:
            self._ui(lambda: self._set_busy(False))

    def _update_alerts(self):
        # Versión async — lanza hilo propio (solo usar cuando NO viene de refresh_all)
        if self._refreshing:
            return
        self._refreshing = True

        def _wrap():
            try:
                self._update_alerts_sync()
            finally:
                self._refreshing = False

        self._run_async(_wrap)

    def _update_alerts_sync(self):
        # Versión síncrona — se ejecuta en el hilo del llamador (segura para secuenciar)
        self._ui(lambda: self._set_busy(True))
        try:
            resp = self.client.get_alerts()
            rows = []
            count = crit = med = 0
            for line in resp.splitlines():
                line = line.strip()
                if not line or "|" not in line:
                    continue
                p = [x.strip() for x in line.split("|")]
                if not self._looks_alert(p):
                    continue
                aid, sensor, tipo, nivel, msg, hora = p[:6]
                tag = "low"
                if nivel.lower() == "high":
                    tag = "high"
                    crit += 1
                elif nivel.lower() == "medium":
                    tag = "medium"
                    med += 1
                rows.append(((aid, sensor, tipo, nivel.upper(), msg, hora), tag))
                count += 1

            snapshot_rows = list(rows)  # Copia inmutable para el closure
            snapshot_count = count
            snapshot_crit = crit
            snapshot_med = med

            def _done():
                self._set_busy(False)
                for item in self.alerts_tree.get_children():
                    self.alerts_tree.delete(item)
                self.alerts_tree.tag_configure(
                    "high", background="#2e0d0d", foreground=self.C["text"]
                )
                self.alerts_tree.tag_configure(
                    "medium", background="#2e2200", foreground=self.C["text"]
                )
                self.alerts_tree.tag_configure(
                    "low", background="#0c2214", foreground=self.C["text"]
                )
                for vals, tag in snapshot_rows:
                    self.alerts_tree.insert("", "end", values=vals, tags=(tag,))
                self.alert_count_var.set(str(snapshot_count))
                self.critical_count_var.set(str(snapshot_crit))
                self.medium_count_var.set(str(snapshot_med))
                self.last_update_var.set(datetime.now().strftime("%H:%M:%S"))
                self.system_state_var.set(
                    "En alerta" if snapshot_count > 0 else "Normal"
                )

            self._ui(_done)
        except Exception:
            self._ui(lambda: self._set_busy(False))

    def _on_ack(self):
        sel = self.alerts_tree.selection()
        if not sel:
            messagebox.showwarning("ACK", "Selecciona una alerta")
            return
        aid = self.alerts_tree.item(sel[0], "values")[0]
        self._set_busy(True)

        def _work():
            try:
                resp = self.client.ack_alert(aid)

                def _done():
                    self._set_busy(False)
                    (messagebox.showinfo if "OK" in resp else messagebox.showwarning)(
                        "ACK", resp
                    )
                    self._update_alerts()

                self._ui(_done)
            except Exception as e:
                self._ui(
                    lambda: (self._set_busy(False), messagebox.showerror("ACK", str(e)))
                )

        self._run_async(_work)

    def _on_clear(self):
        if not messagebox.askyesno(
            "Limpiar alertas", "¿Eliminar todas las alertas activas?"
        ):
            return
        self._set_busy(True)

        def _work():
            try:
                resp = self.client.clear_alerts()

                def _done():
                    self._set_busy(False)
                    self.alert_count_var.set("0")
                    self.critical_count_var.set("0")
                    self.medium_count_var.set("0")
                    self.system_state_var.set("Normal")
                    messagebox.showinfo("Limpiar", resp or "Alertas eliminadas")
                    self._update_alerts()

                self._ui(_done)
            except Exception as e:
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showerror("Limpiar", str(e)),
                    )
                )

        self._run_async(_work)

    def _on_pause(self):
        self._set_busy(True)

        def _work():
            try:
                resp = self.client.pause_simulation()

                def _done():
                    self._set_busy(False)
                    self.sim_state_var.set("Pausado")
                    messagebox.showinfo("Pausar", resp or "Monitoreo pausado")

                self._ui(_done)
            except Exception as e:
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showerror("Pausar", str(e)),
                    )
                )

        self._run_async(_work)

    def _on_resume(self):
        self._set_busy(True)

        def _work():
            try:
                resp = self.client.resume_simulation()

                def _done():
                    self._set_busy(False)
                    self.sim_state_var.set("Activo")
                    messagebox.showinfo("Reanudar", resp or "Monitoreo reanudado")

                self._ui(_done)
            except Exception as e:
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showerror("Reanudar", str(e)),
                    )
                )

        self._run_async(_work)

    def _show_readings(self):
        sel = self.sensors_tree.selection()
        if not sel:
            messagebox.showwarning("Lecturas", "Selecciona un sensor")
            return
        sid = self.sensors_tree.item(sel[0], "values")[0]
        tipo = self.sensors_tree.item(sel[0], "values")[1]
        self._set_busy(True)

        def _work():
            import socket as _s, time as _t

            try:
                sock = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((self.client.host, self.client.port))
                sock.sendall(f"GET_READINGS {sid}\n".encode())
                raw = b""
                _t.sleep(0.1)
                sock.settimeout(1)
                try:
                    while True:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        raw += chunk
                except:
                    pass
                sock.close()
                units = {
                    "co2": "ppm",
                    "ruido": "dB",
                    "temperatura": "C",
                    "pm25": "ug/m3",
                    "humedad": "%",
                    "uv": "idx",
                }
                unit = units.get(tipo.lower(), "")
                lines_out = []
                for line in raw.decode(errors="replace").splitlines():
                    line = line.strip()
                    if (
                        not line
                        or line.upper().startswith("READING")
                        or line.startswith("sin_")
                    ):
                        continue
                    if "|" not in line:
                        continue
                    p = [x.strip() for x in line.split("|")]
                    if len(p) >= 5:
                        try:
                            lines_out.append(
                                f"  {p[4]}   →   {round(float(p[3]),2)} {unit}"
                            )
                        except:
                            pass
                texto = (
                    f"Últimas lecturas — {sid}:\n\n" + "\n".join(lines_out)
                    if lines_out
                    else "Sin datos"
                )
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showinfo(f"Lecturas — {sid}", texto),
                    )
                )
            except Exception as e:
                self._ui(
                    lambda: (
                        self._set_busy(False),
                        messagebox.showerror("Lecturas", str(e)),
                    )
                )

        self._run_async(_work)

    def refresh_all(self, initial=False):
        if self._refreshing and not initial:
            return  # Ciclo anterior aún en curso, ignorar
        self._refreshing = True

        def _work():
            try:
                self._update_sensors_sync()
                self._update_alerts_sync()
            finally:
                self._refreshing = False
                # Si auto-refresh está ON, programar el SIGUIENTE ciclo
                # solo DESPUÉS de que este termine (evita solapamiento)
                if self.auto_refresh_enabled:
                    self._ui(self._reschedule_ar)

        self._run_async(_work)

    def _toggle_ar(self):
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        self.auto_refresh_var.set("ON" if self.auto_refresh_enabled else "OFF")
        self._refresh_ar_button()
        if self.auto_refresh_enabled:
            self._schedule_ar()
        elif self.refresh_job:
            self.root.after_cancel(self.refresh_job)
            self.refresh_job = None

    def _schedule_ar(self):
        # Inicia el primer ciclo; los siguientes los agenda _reschedule_ar al terminar
        if self.auto_refresh_enabled:
            self.refresh_all()

    def _reschedule_ar(self):
        # Llamado desde el hilo de UI al terminar cada ciclo
        if self.auto_refresh_enabled:
            self.refresh_job = self.root.after(5000, self._schedule_ar)


# =============================================================
# FLUJO PRINCIPAL
# =============================================================
def _launch_login():
    import os, argparse, sys
    from operator_client import OperatorClient

    # Prioridad: argumento CLI > variable de entorno > localhost
    parser = argparse.ArgumentParser(
        description="Cliente Operador — Monitoreo Ambiental"
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("IOT_SERVER_HOST", "localhost"),
        help="Host/dominio del servidor (default: IOT_SERVER_HOST o localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("IOT_SERVER_PORT", 5000)),
        help="Puerto del servidor principal (default: 5000)",
    )
    parser.add_argument(
        "--login-host",
        default=os.environ.get("IOT_LOGIN_HOST", None),
        help="Host del login service (default: igual que --host)",
    )
    parser.add_argument(
        "--login-port",
        type=int,
        default=int(os.environ.get("IOT_LOGIN_PORT", 6000)),
        help="Puerto del login service (default: 6000)",
    )
    args, _ = parser.parse_known_args()

    login_host = args.login_host or args.host

    # Resolución de nombres — si falla, avisa pero no cae
    import socket as _sock

    try:
        _sock.getaddrinfo(args.host, args.port)
    except _sock.gaierror as e:
        import tkinter.messagebox as _mb

        _mb.showwarning(
            "DNS",
            f"No se pudo resolver '{args.host}':\n{e}\nIntentando de todas formas...",
        )

    client = OperatorClient(args.host, args.port, login_host, args.login_port)

    try:
        client.connect()
    except Exception as e:
        root_err = tk.Tk()
        root_err.withdraw()
        messagebox.showerror(
            "Error de conexión",
            f"No se puede conectar al servidor en el puerto 5000.\n\n{e}\n\n"
            "Verifica que el servidor esté corriendo.",
        )
        root_err.destroy()
        return

    def on_success(username):
        dash = tk.Tk()
        OperatorGUI(dash, client, username=username)
        dash.mainloop()

    login_root = tk.Tk()
    LoginWindow(login_root, client, on_success=on_success)
    login_root.mainloop()


def main():
    _launch_login()


if __name__ == "__main__":
    main()
