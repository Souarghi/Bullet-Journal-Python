"""Interface graphique moderne pour le Bullet Journal en Tkinter.

Ce module implémente une interface utilisateur graphique complète, responsive
et native (sans aucune dépendance tierce externe) pour manipuler le Bullet Journal :
- Vue quotidienne (Daily Log) avec filtres, badges et actions rapides
- Vue mensuelle (Monthly Log) avec page calendrier et page tâches
- Signifiants (* Priorité, ! Idée) et symboles du Rapid Logging (•, ×, >, ~, ○, –)
- Migration de tâches (jour par jour ou groupée)
- Visionneur de recherche et de journaux (logs)
"""

from __future__ import annotations

from datetime import date, time, timedelta
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from bujo.journal import BulletJournal, DailyLog
from bujo.logger import get_logger
from bujo.models import (
    BujoError,
    Event,
    Signifier,
    TaskStatus,
)

logger = get_logger("gui")


class BujoGUI:
    """Application graphique Tkinter du Bullet Journal."""

    def __init__(self, root: tk.Tk, journal: BulletJournal | None = None) -> None:
        """Initialise la fenêtre et les composants graphiques."""
        self.root = root
        self.journal: BulletJournal = journal or BulletJournal(owner="Utilisateur")

        self.root.title("📖 Bullet Journal (BuJo) - Méthode Ryder Carroll")
        self.root.geometry("1020x680")
        self.root.minsize(860, 560)

        # Dates courantes visualisées
        self.current_day: date = date.today()
        self.current_year: int = date.today().year
        self.current_month: int = date.today().month

        self._apply_theme()
        self._build_ui()
        self.refresh_daily_view()
        self.refresh_monthly_view()
        logger.info("Interface graphique Tkinter initialisée avec succès.")

    def _apply_theme(self) -> None:
        """Configure le thème moderne pour les composants ttk."""
        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if "clam" in available_themes:
            self.style.theme_use("clam")

        self.bg_color = "#f4f5f7"
        self.card_bg = "#ffffff"
        self.text_color = "#1f2937"

        self.root.configure(bg=self.bg_color)

        self.style.configure(
            ".",
            background=self.bg_color,
            foreground=self.text_color,
            font=("Segoe UI", 10),
        )
        self.style.configure("Card.TFrame", background=self.card_bg)
        self.style.configure(
            "Header.TLabel",
            font=("Segoe UI", 14, "bold"),
            background=self.card_bg,
        )
        self.style.configure(
            "SubHeader.TLabel",
            font=("Segoe UI", 11, "bold"),
            background=self.bg_color,
        )

        # Style pour le Treeview
        self.style.configure(
            "Treeview",
            background=self.card_bg,
            foreground=self.text_color,
            rowheight=26,
            fieldbackground=self.card_bg,
            font=("Segoe UI", 10),
        )
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.map(
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", "#1e3a8a")],
        )

    def _build_ui(self) -> None:
        """Construit l'ossature générale de l'application."""
        # 1. En-tête supérieur
        top_bar = ttk.Frame(self.root, style="Card.TFrame", padding=(15, 12))
        top_bar.pack(fill=tk.X, side=tk.TOP, padx=12, pady=(10, 5))

        title_lbl = ttk.Label(
            top_bar,
            text="📖 Bullet Journal (BuJo)",
            style="Header.TLabel",
        )
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = ttk.Label(
            top_bar,
            text=f"  |  Carnet de : {self.journal.owner}",
            font=("Segoe UI", 10, "italic"),
            background=self.card_bg,
            foreground="#6b7280",
        )
        subtitle_lbl.pack(side=tk.LEFT, fill=tk.Y)

        # 2. Onglets principaux (Notebook)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Onglet 1 : Vue du Jour
        self.daily_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.daily_tab, text=" 📅 Vue Quotidienne (Daily Log) ")
        self._build_daily_tab()

        # Onglet 2 : Vue du Mois
        self.monthly_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.monthly_tab, text=" 🗓️ Vue Mensuelle (Monthly Log) ")
        self._build_monthly_tab()

        # Onglet 3 : Recherche & Logs
        self.logs_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.logs_tab, text=" 🔍 Recherche & Logs ")
        self._build_logs_tab()

        # 3. Barre de statut inférieure
        self.status_var = tk.StringVar(value="Prêt. Toutes les opérations sont journalisées.")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            foreground="#6b7280",
            padding=(15, 4),
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # =========================================================================
    # ONGLET 1 : DAILY LOG
    # =========================================================================

    def _build_daily_tab(self) -> None:
        """Construit l'interface du journal quotidien."""
        # Barre de navigation de date
        nav_frame = ttk.Frame(self.daily_tab)
        nav_frame.pack(fill=tk.X, pady=(0, 8))

        btn_prev = ttk.Button(nav_frame, text="◀ Jour précédent", command=self._prev_day)
        btn_prev.pack(side=tk.LEFT, padx=3)

        btn_today = ttk.Button(nav_frame, text="Aujourd'hui", command=self._go_today)
        btn_today.pack(side=tk.LEFT, padx=3)

        btn_next = ttk.Button(nav_frame, text="Jour suivant ▶", command=self._next_day)
        btn_next.pack(side=tk.LEFT, padx=3)

        self.date_label_var = tk.StringVar()
        lbl_date = ttk.Label(
            nav_frame,
            textvariable=self.date_label_var,
            font=("Segoe UI", 12, "bold"),
        )
        lbl_date.pack(side=tk.LEFT, padx=15)

        # Badges compteurs
        self.badge_var = tk.StringVar()
        lbl_badge = ttk.Label(
            nav_frame,
            textvariable=self.badge_var,
            font=("Segoe UI", 9),
            foreground="#374151",
        )
        lbl_badge.pack(side=tk.RIGHT, padx=5)

        # Tableau des entrées (Treeview)
        tree_container = ttk.Frame(self.daily_tab)
        tree_container.pack(fill=tk.BOTH, expand=True)

        columns = ("signifier", "symbol", "id", "type", "title", "details", "category")
        self.daily_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.daily_tree.heading("signifier", text="★")
        self.daily_tree.heading("symbol", text="État")
        self.daily_tree.heading("id", text="ID")
        self.daily_tree.heading("type", text="Type")
        self.daily_tree.heading("title", text="Titre / Intitulé")
        self.daily_tree.heading("details", text="Détails / Description")
        self.daily_tree.heading("category", text="Catégorie")

        self.daily_tree.column("signifier", width=36, anchor="center")
        self.daily_tree.column("symbol", width=50, anchor="center")
        self.daily_tree.column("id", width=80, anchor="center")
        self.daily_tree.column("type", width=85, anchor="center")
        self.daily_tree.column("title", width=320, anchor="w")
        self.daily_tree.column("details", width=260, anchor="w")
        self.daily_tree.column("category", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(
            tree_container,
            orient=tk.VERTICAL,
            command=self.daily_tree.yview,
        )
        self.daily_tree.configure(yscrollcommand=scrollbar.set)
        self.daily_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Boutons d'actions
        action_bar = ttk.Frame(self.daily_tab, padding=(0, 10))
        action_bar.pack(fill=tk.X)

        # Groupe Ajout
        ttk.Button(
            action_bar, text="➕ Tâche", command=self._dialog_add_task
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            action_bar, text="➕ Événement", command=self._dialog_add_event
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            action_bar, text="➕ Note", command=self._dialog_add_note
        ).pack(side=tk.LEFT, padx=3)

        ttk.Separator(action_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        # Groupe Statut
        ttk.Button(
            action_bar, text="✅ Terminer (×)", command=self._mark_selected_done
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            action_bar, text="⏩ Migrer vers demain (>)", command=self._migrate_selected_task
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            action_bar, text="📦 Tout migrer", command=self._migrate_all_today
        ).pack(side=tk.LEFT, padx=3)
        ttk.Button(
            action_bar, text="❌ Abandonner (~)", command=self._mark_selected_cancelled
        ).pack(side=tk.LEFT, padx=3)

        # Groupe Suppression (à droite)
        ttk.Button(
            action_bar, text="🗑️ Supprimer", command=self._remove_selected_entry
        ).pack(side=tk.RIGHT, padx=3)

    def refresh_daily_view(self) -> None:
        """Actualise la liste des entrées et les compteurs pour le jour affiché."""
        self.date_label_var.set(self.current_day.strftime("%A %d %B %Y").capitalize())

        # Vider la liste
        for item in self.daily_tree.get_children():
            self.daily_tree.delete(item)

        daily_log = self.journal.get_daily_log(self.current_day)

        # Compteurs
        tasks = daily_log.get_tasks()
        pending_count = len([t for t in tasks if t.is_pending])
        done_count = len([t for t in tasks if t.is_done])
        migrated_count = len([t for t in tasks if t.status == TaskStatus.MIGRATED])
        cancelled_count = len([t for t in tasks if t.status == TaskStatus.CANCELLED])
        events_count = len(daily_log.get_events())
        notes_count = len(daily_log.get_notes())

        self.badge_var.set(
            f"Tâches : {pending_count} à faire (•) | {done_count} finies (×) | "
            f"{migrated_count} migrées (>) | {cancelled_count} ann. (~) | "
            f"{events_count} évt(s) | {notes_count} note(s)"
        )

        for entry in daily_log.entries:
            sig_symbol = entry.signifier.symbol if entry.signifier else ""
            entry_type = entry.__class__.__name__

            details = entry.description
            if isinstance(entry, Event):
                details_parts = []
                if entry.event_time:
                    details_parts.append(f"Heure: {entry.event_time.strftime('%H:%M')}")
                if entry.location:
                    details_parts.append(f"Lieu: {entry.location}")
                if entry.description:
                    details_parts.append(entry.description)
                details = " | ".join(details_parts)

            self.daily_tree.insert(
                "",
                tk.END,
                iid=entry.id,
                values=(
                    sig_symbol,
                    entry.symbol,
                    entry.id,
                    entry_type,
                    entry.title,
                    details,
                    entry.category or "-",
                ),
            )

    def _prev_day(self) -> None:
        self.current_day -= timedelta(days=1)
        self.refresh_daily_view()

    def _next_day(self) -> None:
        self.current_day += timedelta(days=1)
        self.refresh_daily_view()

    def _go_today(self) -> None:
        self.current_day = date.today()
        self.refresh_daily_view()

    def _get_selected_entry_id(self) -> str | None:
        selected = self.daily_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Sélection requise",
                "Veuillez sélectionner un élément dans la liste.",
            )
            return None
        return selected[0]

    # =========================================================================
    # ACTIONS RAPIDES DU DAILY LOG
    # =========================================================================

    def _dialog_add_task(self) -> None:
        """Ouvre une boîte de dialogue pour créer une nouvelle tâche."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ajouter une tâche")
        dialog.geometry("400x260")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog, text="Titre de la tâche :", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 2))
        title_entry = ttk.Entry(dialog, width=45)
        title_entry.pack(fill=tk.X, padx=15)
        title_entry.focus_set()

        ttk.Label(dialog, text="Description optionnelle :").pack(anchor="w", padx=15, pady=(8, 2))
        desc_entry = ttk.Entry(dialog, width=45)
        desc_entry.pack(fill=tk.X, padx=15)

        ttk.Label(dialog, text="Catégorie optionnelle :").pack(anchor="w", padx=15, pady=(8, 2))
        cat_entry = ttk.Entry(dialog, width=45)
        cat_entry.pack(fill=tk.X, padx=15)

        # Sélecteur de signifiant
        ttk.Label(dialog, text="Signifiant (priorité / idée) :").pack(
            anchor="w", padx=15, pady=(8, 2)
        )
        sig_var = tk.StringVar(value="Aucun")
        sig_combo = ttk.Combobox(
            dialog,
            textvariable=sig_var,
            values=["Aucun", "* Priorité", "! Idée"],
            state="readonly",
            width=20,
        )
        sig_combo.pack(anchor="w", padx=15)

        def save() -> None:
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror("Erreur", "Le titre ne peut pas être vide.", parent=dialog)
                return
            desc = desc_entry.get().strip()
            cat = cat_entry.get().strip() or None

            sig_choice = sig_var.get()
            signifier = None
            if sig_choice.startswith("*"):
                signifier = Signifier.PRIORITY
            elif sig_choice.startswith("!"):
                signifier = Signifier.IDEA

            try:
                daily_log = self.journal.get_daily_log(self.current_day)
                daily_log.add_task(
                    title=title,
                    description=desc,
                    category=cat,
                    signifier=signifier,
                )
                self.refresh_daily_view()
                self.status_var.set(
                    f"Tâche '{title}' ajoutée avec succès au {self.current_day}."
                )
                dialog.destroy()
            except BujoError as e:
                messagebox.showerror("Erreur", str(e), parent=dialog)

        btn_box = ttk.Frame(dialog)
        btn_box.pack(fill=tk.X, pady=15, padx=15)
        ttk.Button(btn_box, text="Enregistrer", command=save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_box, text="Annuler", command=dialog.destroy).pack(side=tk.RIGHT, padx=4)

    def _dialog_add_event(self) -> None:
        """Ouvre une boîte de dialogue pour créer un événement."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ajouter un événement")
        dialog.geometry("400x310")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog, text="Intitulé de l'événement :", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 2))
        title_entry = ttk.Entry(dialog, width=45)
        title_entry.pack(fill=tk.X, padx=15)
        title_entry.focus_set()

        ttk.Label(dialog, text="Heure (HH:MM, optionnel) :").pack(
            anchor="w", padx=15, pady=(8, 2)
        )
        time_entry = ttk.Entry(dialog, width=15)
        time_entry.pack(anchor="w", padx=15)

        ttk.Label(dialog, text="Lieu optionnel :").pack(anchor="w", padx=15, pady=(8, 2))
        loc_entry = ttk.Entry(dialog, width=45)
        loc_entry.pack(fill=tk.X, padx=15)

        ttk.Label(dialog, text="Description optionnelle :").pack(anchor="w", padx=15, pady=(8, 2))
        desc_entry = ttk.Entry(dialog, width=45)
        desc_entry.pack(fill=tk.X, padx=15)

        def save() -> None:
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror("Erreur", "L'intitulé ne peut pas être vide.", parent=dialog)
                return

            event_time = None
            t_str = time_entry.get().strip()
            if t_str:
                try:
                    parts = t_str.split(":")
                    event_time = time(int(parts[0]), int(parts[1]))
                except Exception:
                    messagebox.showerror(
                        "Erreur",
                        "Format d'heure invalide. Utilisez HH:MM (ex: 14:30).",
                        parent=dialog,
                    )
                    return

            loc = loc_entry.get().strip() or None
            desc = desc_entry.get().strip()

            try:
                daily_log = self.journal.get_daily_log(self.current_day)
                daily_log.add_event(
                    title=title,
                    event_date=self.current_day,
                    event_time=event_time,
                    description=desc,
                    location=loc,
                )
                self.refresh_daily_view()
                self.status_var.set(f"Événement '{title}' ajouté au {self.current_day}.")
                dialog.destroy()
            except BujoError as e:
                messagebox.showerror("Erreur", str(e), parent=dialog)

        btn_box = ttk.Frame(dialog)
        btn_box.pack(fill=tk.X, pady=15, padx=15)
        ttk.Button(btn_box, text="Enregistrer", command=save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_box, text="Annuler", command=dialog.destroy).pack(side=tk.RIGHT, padx=4)

    def _dialog_add_note(self) -> None:
        """Ouvre une boîte de dialogue pour créer une note."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ajouter une note")
        dialog.geometry("400x240")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog, text="Titre de la note :", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 2))
        title_entry = ttk.Entry(dialog, width=45)
        title_entry.pack(fill=tk.X, padx=15)
        title_entry.focus_set()

        ttk.Label(
            dialog, text="Contenu / Détails de la réflexion :"
        ).pack(anchor="w", padx=15, pady=(8, 2))
        desc_entry = ttk.Entry(dialog, width=45)
        desc_entry.pack(fill=tk.X, padx=15)

        ttk.Label(dialog, text="Signifiant :").pack(anchor="w", padx=15, pady=(8, 2))
        sig_var = tk.StringVar(value="! Idée")
        sig_combo = ttk.Combobox(
            dialog,
            textvariable=sig_var,
            values=["Aucun", "! Idée", "* Priorité"],
            state="readonly",
            width=15,
        )
        sig_combo.pack(anchor="w", padx=15)

        def save() -> None:
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror(
                    "Erreur", "Le titre de la note ne peut pas être vide.", parent=dialog
                )
                return
            desc = desc_entry.get().strip()
            sig_choice = sig_var.get()
            sig = (
                Signifier.IDEA
                if sig_choice.startswith("!")
                else (Signifier.PRIORITY if sig_choice.startswith("*") else None)
            )

            try:
                daily_log = self.journal.get_daily_log(self.current_day)
                daily_log.add_note(title=title, description=desc, signifier=sig)
                self.refresh_daily_view()
                self.status_var.set(f"Note '{title}' consignée au {self.current_day}.")
                dialog.destroy()
            except BujoError as e:
                messagebox.showerror("Erreur", str(e), parent=dialog)

        btn_box = ttk.Frame(dialog)
        btn_box.pack(fill=tk.X, pady=15, padx=15)
        ttk.Button(btn_box, text="Enregistrer", command=save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_box, text="Annuler", command=dialog.destroy).pack(side=tk.RIGHT, padx=4)

    def _mark_selected_done(self) -> None:
        entry_id = self._get_selected_entry_id()
        if not entry_id:
            return
        try:
            daily_log = self.journal.get_daily_log(self.current_day)
            daily_log.mark_task_done(entry_id)
            self.refresh_daily_view()
            self.status_var.set(f"Tâche {entry_id} marquée comme terminée (×).")
        except BujoError as e:
            messagebox.showerror("Action impossible", str(e))

    def _mark_selected_cancelled(self) -> None:
        entry_id = self._get_selected_entry_id()
        if not entry_id:
            return
        try:
            daily_log = self.journal.get_daily_log(self.current_day)
            daily_log.mark_task_cancelled(entry_id)
            self.refresh_daily_view()
            self.status_var.set(f"Tâche {entry_id} abandonnée (~).")
        except BujoError as e:
            messagebox.showerror("Action impossible", str(e))

    def _migrate_selected_task(self) -> None:
        """Migre la tâche sélectionnée vers le lendemain."""
        entry_id = self._get_selected_entry_id()
        if not entry_id:
            return

        next_day = self.current_day + timedelta(days=1)
        confirm = messagebox.askyesno(
            "Confirmer la migration",
            f"Voulez-vous reporter cette tâche vers le {next_day.strftime('%d/%m/%Y')} ?\n\n"
            "• La tâche actuelle passera au statut Migrée (>).\n"
            "• Une nouvelle tâche active (•) sera créée sur le journal de demain.",
        )
        if not confirm:
            return

        try:
            source_log = self.journal.get_daily_log(self.current_day)
            target_log = self.journal.get_daily_log(next_day)
            new_task = source_log.migrate_task(entry_id, target_log)
            self.refresh_daily_view()
            self.status_var.set(
                f"Tâche {entry_id} migrée avec succès vers le {next_day} "
                f"(nouvel ID: {new_task.id})."
            )
        except BujoError as e:
            messagebox.showerror("Migration impossible", str(e))

    def _migrate_all_today(self) -> None:
        """Migre toutes les tâches non terminées d'aujourd'hui vers demain."""
        daily_log = self.journal.get_daily_log(self.current_day)
        pending = daily_log.get_pending_tasks()
        if not pending:
            messagebox.showinfo(
                "Information",
                "Aucune tâche en attente à migrer pour cette journée.",
            )
            return

        next_day = self.current_day + timedelta(days=1)
        confirm = messagebox.askyesno(
            "Migration collective",
            f"Migrer {len(pending)} tâche(s) en attente vers demain "
            f"({next_day.strftime('%d/%m/%Y')}) ?",
        )
        if not confirm:
            return

        target_log = self.journal.get_daily_log(next_day)
        migrated = daily_log.migrate_pending_tasks(target_log)
        self.refresh_daily_view()
        self.status_var.set(f"{len(migrated)} tâche(s) reportée(s) au {next_day}.")

    def _remove_selected_entry(self) -> None:
        entry_id = self._get_selected_entry_id()
        if not entry_id:
            return
        if not messagebox.askyesno(
            "Confirmation", f"Supprimer définitivement l'entrée {entry_id} ?"
        ):
            return
        try:
            daily_log = self.journal.get_daily_log(self.current_day)
            daily_log.remove_entry(entry_id)
            self.refresh_daily_view()
            self.status_var.set(f"Entrée {entry_id} supprimée.")
        except BujoError as e:
            messagebox.showerror("Erreur de suppression", str(e))

    # =========================================================================
    # ONGLET 2 : MONTHLY LOG
    # =========================================================================

    def _build_monthly_tab(self) -> None:
        """Construit l'interface du journal mensuel (Calendrier + Tâches)."""
        nav_frame = ttk.Frame(self.monthly_tab)
        nav_frame.pack(fill=tk.X, pady=(0, 8))

        btn_prev = ttk.Button(nav_frame, text="◀ Mois précédent", command=self._prev_month)
        btn_prev.pack(side=tk.LEFT, padx=3)

        btn_cur = ttk.Button(nav_frame, text="Mois en cours", command=self._cur_month)
        btn_cur.pack(side=tk.LEFT, padx=3)

        btn_next = ttk.Button(nav_frame, text="Mois suivant ▶", command=self._next_month)
        btn_next.pack(side=tk.LEFT, padx=3)

        self.month_label_var = tk.StringVar()
        lbl_month = ttk.Label(
            nav_frame,
            textvariable=self.month_label_var,
            font=("Segoe UI", 12, "bold"),
        )
        lbl_month.pack(side=tk.LEFT, padx=15)

        # Boutons d'actions mensuelles
        btn_add_task_m = ttk.Button(
            nav_frame,
            text="➕ Tâche mensuelle",
            command=self._dialog_add_monthly_task,
        )
        btn_add_task_m.pack(side=tk.RIGHT, padx=3)

        btn_mig_m = ttk.Button(
            nav_frame,
            text="⏩ Migrer vers mois suivant",
            command=self._migrate_monthly_tasks,
        )
        btn_mig_m.pack(side=tk.RIGHT, padx=3)

        # Conteneur séparé en deux colonnes
        paned = ttk.PanedWindow(self.monthly_tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Volet gauche : Page Calendrier
        cal_frame = ttk.Frame(paned, padding=5)
        paned.add(cal_frame, weight=1)

        ttk.Label(
            cal_frame,
            text="📅 Page Calendrier & Événements",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        self.cal_text = tk.Text(
            cal_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#ffffff",
        )
        cal_scroll = ttk.Scrollbar(
            cal_frame,
            orient=tk.VERTICAL,
            command=self.cal_text.yview,
        )
        self.cal_text.configure(yscrollcommand=cal_scroll.set)
        self.cal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cal_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Volet droit : Page Tâches du Mois
        task_frame = ttk.Frame(paned, padding=5)
        paned.add(task_frame, weight=1)

        ttk.Label(
            task_frame,
            text="📋 Page Tâches du Mois",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        self.month_task_text = tk.Text(
            task_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#ffffff",
        )
        task_scroll = ttk.Scrollbar(
            task_frame,
            orient=tk.VERTICAL,
            command=self.month_task_text.yview,
        )
        self.month_task_text.configure(yscrollcommand=task_scroll.set)
        self.month_task_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_monthly_view(self) -> None:
        """Actualise la page Calendrier et la page Tâches du mois."""
        monthly_log = self.journal.get_monthly_log(self.current_year, self.current_month)
        self.month_label_var.set(monthly_log.name)

        # 1. Rendu Calendrier
        self.cal_text.delete("1.0", tk.END)
        self.cal_text.insert(tk.END, monthly_log.calendar_view())

        # 2. Rendu Tâches
        self.month_task_text.delete("1.0", tk.END)
        self.month_task_text.insert(tk.END, monthly_log.task_view())

    def _prev_month(self) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh_monthly_view()

    def _next_month(self) -> None:
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh_monthly_view()

    def _cur_month(self) -> None:
        today = date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.refresh_monthly_view()

    def _dialog_add_monthly_task(self) -> None:
        """Ajoute une tâche mensuelle."""
        title = simpledialog.askstring(
            "Nouvelle Tâche Mensuelle",
            "Titre de la tâche :",
            parent=self.root,
        )
        if not title or not title.strip():
            return
        monthly_log = self.journal.get_monthly_log(self.current_year, self.current_month)
        monthly_log.add_task(title=title.strip())
        self.refresh_monthly_view()
        self.status_var.set(
            f"Tâche mensuelle '{title.strip()}' ajoutée pour {monthly_log.name}."
        )

    def _migrate_monthly_tasks(self) -> None:
        """Migre les tâches non faites de ce mois vers le mois suivant."""
        monthly_log = self.journal.get_monthly_log(self.current_year, self.current_month)
        pending = monthly_log.get_pending_tasks()
        if not pending:
            messagebox.showinfo(
                "Information",
                "Aucune tâche mensuelle en attente à migrer.",
            )
            return

        next_m = 1 if self.current_month == 12 else self.current_month + 1
        next_y = self.current_year + 1 if self.current_month == 12 else self.current_year
        next_log = self.journal.get_monthly_log(next_y, next_m)

        if not messagebox.askyesno(
            "Migration mensuelle",
            f"Migrer {len(pending)} tâche(s) du mois vers {next_log.name} ?",
        ):
            return

        migrated = monthly_log.migrate_pending_tasks(next_log)
        self.refresh_monthly_view()
        self.status_var.set(f"{len(migrated)} tâche(s) reportée(s) sur {next_log.name}.")

    # =========================================================================
    # ONGLET 3 : RECHERCHE & LOGS
    # =========================================================================

    def _build_logs_tab(self) -> None:
        """Construit l'onglet d'inspection des logs et de recherche."""
        search_frame = ttk.Frame(self.logs_tab)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            search_frame,
            text="Recherche d'une entrée par ID :",
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=5)
        self.search_id_entry = ttk.Entry(search_frame, width=20)
        self.search_id_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            search_frame, text="🔍 Trouver", command=self._search_entry
        ).pack(side=tk.LEFT, padx=5)

        self.search_result_var = tk.StringVar(value="")
        lbl_res = ttk.Label(
            self.logs_tab,
            textvariable=self.search_result_var,
            font=("Segoe UI", 10, "italic"),
            foreground="#1e40af",
        )
        lbl_res.pack(anchor="w", pady=(0, 8))

        # Séparateur
        ttk.Separator(self.logs_tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        # Visionneur des fichiers de logs
        log_header = ttk.Frame(self.logs_tab)
        log_header.pack(fill=tk.X, pady=(4, 4))

        ttk.Label(
            log_header,
            text="📑 Fichiers de Journalisation (logs/debug.log & logs/errors.log)",
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)
        ttk.Button(
            log_header,
            text="🔄 Actualiser les logs",
            command=self._refresh_log_viewer,
        ).pack(side=tk.RIGHT)

        self.log_text = tk.Text(
            self.logs_tab,
            wrap=tk.NONE,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
        )
        log_scroll = ttk.Scrollbar(
            self.logs_tab,
            orient=tk.VERTICAL,
            command=self.log_text.yview,
        )
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._refresh_log_viewer()

    def _search_entry(self) -> None:
        target_id = self.search_id_entry.get().strip()
        if not target_id:
            messagebox.showwarning("ID manquant", "Veuillez entrer un ID à rechercher.")
            return

        try:
            container, entry = self.journal.find_entry(target_id)
            loc = (
                f"Daily Log du {container.log_date}"
                if isinstance(container, DailyLog)
                else f"Monthly Log {container.name}"
            )
            self.search_result_var.set(
                f"Trouvé dans : {loc}\n→ {entry.display()}"
            )
        except BujoError as e:
            self.search_result_var.set(f"❌ {e}")

    def _refresh_log_viewer(self) -> None:
        """Lit et affiche les dernières lignes des fichiers de log."""
        self.log_text.delete("1.0", tk.END)
        debug_path = os.path.join("logs", "debug.log")
        errors_path = os.path.join("logs", "errors.log")

        content = []
        if os.path.exists(errors_path):
            try:
                with open(errors_path, "r", encoding="utf-8") as f:
                    err_lines = f.readlines()
                    if err_lines:
                        content.append("=== ERREURS & ANOMALIES (logs/errors.log) ===")
                        content.extend(err_lines[-15:])
                        content.append("\n")
            except Exception as e:
                content.append(f"Erreur de lecture errors.log : {e}\n")

        if os.path.exists(debug_path):
            try:
                with open(debug_path, "r", encoding="utf-8") as f:
                    deb_lines = f.readlines()
                    content.append("=== DERNIÈRES ACTIONS (logs/debug.log) ===")
                    content.extend(deb_lines[-30:])
            except Exception as e:
                content.append(f"Erreur de lecture debug.log : {e}\n")

        if not content:
            content.append("(Aucun log enregistré pour l'instant)")

        self.log_text.insert(tk.END, "".join(content))
        self.log_text.see(tk.END)


def launch_gui(journal: BulletJournal | None = None) -> None:
    """Lance l'application graphique Tkinter."""
    root = tk.Tk()
    BujoGUI(root, journal=journal)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
