"""Traduzioni dell'interfaccia (6 lingue) — tutto il testo fisso del sito.

Lingue: it (italiano), en (inglese), es (spagnolo), fr (francese), de (tedesco),
uk (ucraino). Cambi lingua in Impostazioni o dalla barra in alto e TUTTA
l'interfaccia si traduce.

Cosa NON si traduce qui: i dati che inserisci tu (note, nomi che digiti). Le
categorie precaricate da noi sono invece tradotte (vedi CATEGORIES).

Uso nei template: {{ t('chiave') }} oppure {{ t('chiave', var=...) }} e
{{ t.category(nome_categoria) }}.
"""

LANGS = [
    ("it", "Italiano"),
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("uk", "Українська"),
]
LANG_CODES = [c for c, _ in LANGS]
DEFAULT_LANG = "it"

# Ogni chiave ha le sue 6 traduzioni. Se manca una lingua si ripiega sull'italiano.
STRINGS = {
    # ---- marchio / navigazione / comune ----
    "app.name": {"it": "Finanza personale", "en": "Personal Finance", "es": "Finanzas personales", "fr": "Finances personnelles", "de": "Persönliche Finanzen", "uk": "Особисті фінанси"},
    "brand.private": {"it": "uso privato", "en": "private use", "es": "uso privado", "fr": "usage privé", "de": "privat", "uk": "приватне використання"},
    "nav.dashboard": {"it": "Dashboard", "en": "Dashboard", "es": "Panel", "fr": "Tableau de bord", "de": "Übersicht", "uk": "Панель"},
    "nav.portfolio": {"it": "Portafoglio", "en": "Portfolio", "es": "Cartera", "fr": "Portefeuille", "de": "Portfolio", "uk": "Портфель"},
    "nav.pac": {"it": "Calcolatore PAC", "en": "DCA calculator", "es": "Calculadora DCA", "fr": "Calculateur DCA", "de": "Sparplan-Rechner", "uk": "Калькулятор DCA"},
    "nav.finance": {"it": "Finanze", "en": "Finances", "es": "Finanzas", "fr": "Finances", "de": "Finanzen", "uk": "Фінанси"},
    "nav.news": {"it": "Notizie", "en": "News", "es": "Noticias", "fr": "Actualités", "de": "Nachrichten", "uk": "Новини"},
    "nav.settings": {"it": "Impostazioni", "en": "Settings", "es": "Ajustes", "fr": "Paramètres", "de": "Einstellungen", "uk": "Налаштування"},
    "nav.soon": {"it": "presto", "en": "soon", "es": "pronto", "fr": "bientôt", "de": "bald", "uk": "скоро"},
    "common.total": {"it": "Totale", "en": "Total", "es": "Total", "fr": "Total", "de": "Gesamt", "uk": "Разом"},
    "theme.toggle": {"it": "Cambia tema chiaro/scuro", "en": "Toggle light/dark theme", "es": "Cambiar tema claro/oscuro", "fr": "Basculer thème clair/sombre", "de": "Hell/Dunkel umschalten", "uk": "Перемкнути світлу/темну тему"},
    "theme.light": {"it": "Chiaro", "en": "Light", "es": "Claro", "fr": "Clair", "de": "Hell", "uk": "Світла"},
    "theme.dark": {"it": "Scuro", "en": "Dark", "es": "Oscuro", "fr": "Sombre", "de": "Dunkel", "uk": "Темна"},
    "lang.label": {"it": "Lingua", "en": "Language", "es": "Idioma", "fr": "Langue", "de": "Sprache", "uk": "Мова"},
    "type.etf": {"it": "ETF", "en": "ETF", "es": "ETF", "fr": "ETF", "de": "ETF", "uk": "ETF"},
    "type.stock": {"it": "Azione", "en": "Stock", "es": "Acción", "fr": "Action", "de": "Aktie", "uk": "Акція"},

    "disclaimer.text": {
        "it": "Strumento personale di informazione e organizzazione, non un consiglio finanziario e non un segnale operativo di acquisto/vendita. I dati e le analisi servono a capire, non a dire cosa fare: la decisione resta sempre tua. Eventuali analisi generate dall'AI sono etichettate come tali e accompagnate da un livello di confidenza. I valori non disponibili restano vuoti, mai inventati.",
        "en": "Personal information and organization tool, not financial advice and not a buy/sell signal. Data and analyses are meant to help you understand, not to tell you what to do: the decision is always yours. Any AI-generated analysis is labeled as such and comes with a confidence level. Unavailable values are left blank, never made up.",
        "es": "Herramienta personal de información y organización, no asesoramiento financiero ni una señal de compra/venta. Los datos y análisis sirven para entender, no para decirte qué hacer: la decisión es siempre tuya. Cualquier análisis generado por IA se etiqueta como tal y se acompaña de un nivel de confianza. Los valores no disponibles se dejan en blanco, nunca se inventan.",
        "fr": "Outil personnel d'information et d'organisation, pas un conseil financier ni un signal d'achat/vente. Les données et analyses servent à comprendre, pas à dicter quoi faire : la décision reste toujours la vôtre. Toute analyse générée par l'IA est signalée comme telle et accompagnée d'un niveau de confiance. Les valeurs non disponibles restent vides, jamais inventées.",
        "de": "Persönliches Informations- und Organisationswerkzeug, keine Finanzberatung und kein Kauf-/Verkaufssignal. Daten und Analysen dienen dem Verständnis, nicht der Handlungsanweisung: Die Entscheidung bleibt immer bei dir. Von der KI erzeugte Analysen sind als solche gekennzeichnet und mit einem Konfidenzniveau versehen. Nicht verfügbare Werte bleiben leer und werden nie erfunden.",
        "uk": "Особистий інструмент інформування та організації, а не фінансова порада і не сигнал на купівлю/продаж. Дані й аналітика допомагають зрозуміти, а не вказують, що робити: рішення завжди за тобою. Будь-яка згенерована ШІ аналітика позначається як така й супроводжується рівнем впевненості. Недоступні значення залишаються порожніми, їх ніколи не вигадують.",
    },

    # ---- dashboard ----
    "dash.subtitle": {"it": "Panoramica del tuo sistema. Le sezioni si attivano una alla volta, fase per fase.", "en": "Overview of your system. Sections come online one at a time, phase by phase.", "es": "Resumen de tu sistema. Las secciones se activan una a una, fase por fase.", "fr": "Vue d'ensemble de ton système. Les sections s'activent une à une, phase par phase.", "de": "Überblick über dein System. Die Bereiche werden nach und nach freigeschaltet, Phase für Phase.", "uk": "Огляд твоєї системи. Розділи вмикаються по черзі, фаза за фазою."},
    "dash.stat_positions": {"it": "Posizioni in portafoglio", "en": "Positions in portfolio", "es": "Posiciones en cartera", "fr": "Positions en portefeuille", "de": "Positionen im Portfolio", "uk": "Позиції в портфелі"},
    "dash.etf_stocks": {"it": "{etf} ETF · {stocks} azioni", "en": "{etf} ETFs · {stocks} stocks", "es": "{etf} ETF · {stocks} acciones", "fr": "{etf} ETF · {stocks} actions", "de": "{etf} ETFs · {stocks} Aktien", "uk": "{etf} ETF · {stocks} акцій"},
    "dash.stat_target": {"it": "Totale % target", "en": "Total target %", "es": "Total % objetivo", "fr": "Total % cible", "de": "Gesamt-Zielanteil %", "uk": "Загальний цільовий %"},
    "dash.target_ok": {"it": "✓ allocazione completa (100%)", "en": "✓ allocation complete (100%)", "es": "✓ asignación completa (100%)", "fr": "✓ allocation complète (100%)", "de": "✓ Allokation vollständig (100%)", "uk": "✓ розподіл повний (100%)"},
    "dash.target_warn": {"it": "⚠ non fa 100%, controlla", "en": "⚠ not 100%, please check", "es": "⚠ no suma 100%, revisa", "fr": "⚠ pas 100%, à vérifier", "de": "⚠ nicht 100%, bitte prüfen", "uk": "⚠ не 100%, перевір"},
    "dash.stat_value": {"it": "Valore posseduto inserito", "en": "Holdings value entered", "es": "Valor poseído introducido", "fr": "Valeur détenue saisie", "de": "Erfasster Bestandswert", "uk": "Введена вартість активів"},
    "dash.value_todo": {"it": "da compilare quando vuoi", "en": "fill in whenever you like", "es": "rellénalo cuando quieras", "fr": "à remplir quand tu veux", "de": "jederzeit ausfüllbar", "uk": "заповни коли захочеш"},
    "dash.value_sum": {"it": "somma dei valori inseriti a mano", "en": "sum of manually entered values", "es": "suma de los valores introducidos a mano", "fr": "somme des valeurs saisies à la main", "de": "Summe der manuell eingegebenen Werte", "uk": "сума введених вручну значень"},
    "dash.build_h": {"it": "Stato di costruzione", "en": "Build status", "es": "Estado de construcción", "fr": "État de construction", "de": "Aufbaustatus", "uk": "Стан розробки"},
    "dash.build_title": {"it": "Cosa è già pronto e cosa arriva", "en": "What's ready and what's coming", "es": "Qué está listo y qué llega", "fr": "Ce qui est prêt et ce qui arrive", "de": "Was fertig ist und was kommt", "uk": "Що готово і що попереду"},
    "dash.build_using": {"it": "Stai usando le basi: portafoglio, calcolatore PAC, tema e multilingua. Tutto offline.", "en": "You're using the foundations: portfolio, DCA calculator, theme and multilingual UI. All offline.", "es": "Estás usando las bases: cartera, calculadora DCA, tema e interfaz multilingüe. Todo sin conexión.", "fr": "Tu utilises les fondations : portefeuille, calculateur DCA, thème et interface multilingue. Tout hors ligne.", "de": "Du nutzt die Grundlagen: Portfolio, Sparplan-Rechner, Theme und mehrsprachige Oberfläche. Alles offline.", "uk": "Ти використовуєш основи: портфель, калькулятор DCA, тему та багатомовний інтерфейс. Усе офлайн."},
    "dash.pill_portfolio": {"it": "✓ Portafoglio (posizioni)", "en": "✓ Portfolio (positions)", "es": "✓ Cartera (posiciones)", "fr": "✓ Portefeuille (positions)", "de": "✓ Portfolio (Positionen)", "uk": "✓ Портфель (позиції)"},
    "dash.pill_pac": {"it": "✓ Calcolatore PAC", "en": "✓ DCA calculator", "es": "✓ Calculadora DCA", "fr": "✓ Calculateur DCA", "de": "✓ Sparplan-Rechner", "uk": "✓ Калькулятор DCA"},
    "dash.pill_theme": {"it": "✓ Tema e lingue", "en": "✓ Theme & languages", "es": "✓ Tema e idiomas", "fr": "✓ Thème et langues", "de": "✓ Theme & Sprachen", "uk": "✓ Тема та мови"},
    "dash.pill_prices": {"it": "Prezzi & dati di mercato — Fase 2", "en": "Prices & market data — Phase 2", "es": "Precios y datos de mercado — Fase 2", "fr": "Prix et données de marché — Phase 2", "de": "Kurse & Marktdaten — Phase 2", "uk": "Ціни та ринкові дані — Фаза 2"},
    "dash.pill_finance": {"it": "Finanze (entrate/uscite) — Fase 3", "en": "Finances (income/expenses) — Phase 3", "es": "Finanzas (ingresos/gastos) — Fase 3", "fr": "Finances (revenus/dépenses) — Phase 3", "de": "Finanzen (Einnahmen/Ausgaben) — Phase 3", "uk": "Фінанси (доходи/витрати) — Фаза 3"},
    "dash.pill_ai": {"it": "Agente AI — Fase 4", "en": "AI assistant — Phase 4", "es": "Asistente IA — Fase 4", "fr": "Assistant IA — Phase 4", "de": "KI-Assistent — Phase 4", "uk": "ШІ-помічник — Фаза 4"},
    "dash.pill_news": {"it": "Notizie — Fase 5", "en": "News — Phase 5", "es": "Noticias — Fase 5", "fr": "Actualités — Phase 5", "de": "Nachrichten — Phase 5", "uk": "Новини — Фаза 5"},
    "dash.btn_portfolio": {"it": "Vai al portafoglio", "en": "Go to portfolio", "es": "Ir a la cartera", "fr": "Aller au portefeuille", "de": "Zum Portfolio", "uk": "До портфеля"},
    "dash.btn_pac": {"it": "Apri il calcolatore PAC", "en": "Open the DCA calculator", "es": "Abrir la calculadora DCA", "fr": "Ouvrir le calculateur DCA", "de": "Sparplan-Rechner öffnen", "uk": "Відкрити калькулятор DCA"},

    # ---- portafoglio (elenco) ----
    "pf.subtitle": {"it": "Le tue posizioni e l'allocazione target. Aggiungi, modifica ed elimina tutto da qui.", "en": "Your positions and target allocation. Add, edit and delete everything here.", "es": "Tus posiciones y la asignación objetivo. Añade, edita y elimina todo desde aquí.", "fr": "Tes positions et l'allocation cible. Ajoute, modifie et supprime tout ici.", "de": "Deine Positionen und die Zielallokation. Hier kannst du alles hinzufügen, bearbeiten und löschen.", "uk": "Твої позиції та цільовий розподіл. Додавай, редагуй і видаляй усе тут."},
    "pf.warn_not100": {"it": "⚠ La somma delle % target fa {pct}, non 100%. Va benissimo mentre stai sistemando le quote — il calcolatore PAC te lo ricorderà.", "en": "⚠ Target % sum is {pct}, not 100%. That's fine while you're adjusting the weights — the DCA calculator will remind you.", "es": "⚠ La suma de % objetivo es {pct}, no 100%. No pasa nada mientras ajustas los pesos — la calculadora DCA te lo recordará.", "fr": "⚠ La somme des % cibles est {pct}, pas 100%. Pas de souci pendant que tu ajustes les pondérations — le calculateur DCA te le rappellera.", "de": "⚠ Summe der Ziel-% beträgt {pct}, nicht 100%. Das ist in Ordnung, während du die Gewichte anpasst — der Sparplan-Rechner erinnert dich daran.", "uk": "⚠ Сума цільових % дорівнює {pct}, а не 100%. Це нормально, поки ти налаштовуєш ваги — калькулятор DCA нагадає тобі."},
    "pf.btn_add": {"it": "+ Aggiungi posizione", "en": "+ Add position", "es": "+ Añadir posición", "fr": "+ Ajouter une position", "de": "+ Position hinzufügen", "uk": "+ Додати позицію"},
    "pf.count": {"it": "{n} posizioni · {etf} ETF · {stocks} azioni", "en": "{n} positions · {etf} ETFs · {stocks} stocks", "es": "{n} posiciones · {etf} ETF · {stocks} acciones", "fr": "{n} positions · {etf} ETF · {stocks} actions", "de": "{n} Positionen · {etf} ETFs · {stocks} Aktien", "uk": "{n} позицій · {etf} ETF · {stocks} акцій"},
    "th.title": {"it": "Titolo", "en": "Security", "es": "Título", "fr": "Titre", "de": "Wertpapier", "uk": "Цінний папір"},
    "th.category": {"it": "Categoria / Tema", "en": "Category / Theme", "es": "Categoría / Tema", "fr": "Catégorie / Thème", "de": "Kategorie / Thema", "uk": "Категорія / Тема"},
    "th.pct_target": {"it": "% Target", "en": "Target %", "es": "% Objetivo", "fr": "% Cible", "de": "Ziel-%", "uk": "Цільовий %"},
    "th.qty": {"it": "Quantità", "en": "Quantity", "es": "Cantidad", "fr": "Quantité", "de": "Menge", "uk": "Кількість"},
    "th.value": {"it": "Valore", "en": "Value", "es": "Valor", "fr": "Valeur", "de": "Wert", "uk": "Вартість"},
    "th.last_buy": {"it": "Ultimo acquisto", "en": "Last purchase", "es": "Última compra", "fr": "Dernier achat", "de": "Letzter Kauf", "uk": "Остання купівля"},
    "th.actions": {"it": "Azioni", "en": "Actions", "es": "Acciones", "fr": "Actions", "de": "Aktionen", "uk": "Дії"},
    "pf.fixed_month": {"it": "{eur}/mese fisso", "en": "{eur}/month fixed", "es": "{eur}/mes fijo", "fr": "{eur}/mois fixe", "de": "{eur}/Monat fest", "uk": "{eur}/міс фіксовано"},
    "pf.isin": {"it": "ISIN {isin}", "en": "ISIN {isin}", "es": "ISIN {isin}", "fr": "ISIN {isin}", "de": "ISIN {isin}", "uk": "ISIN {isin}"},
    "btn.edit": {"it": "Modifica", "en": "Edit", "es": "Editar", "fr": "Modifier", "de": "Bearbeiten", "uk": "Редагувати"},
    "btn.delete": {"it": "Elimina", "en": "Delete", "es": "Eliminar", "fr": "Supprimer", "de": "Löschen", "uk": "Видалити"},
    "pf.confirm_delete": {"it": "Eliminare questa posizione? L'operazione non è reversibile.", "en": "Delete this position? This cannot be undone.", "es": "¿Eliminar esta posición? Esta acción no se puede deshacer.", "fr": "Supprimer cette position ? Action irréversible.", "de": "Diese Position löschen? Das kann nicht rückgängig gemacht werden.", "uk": "Видалити цю позицію? Цю дію не можна скасувати."},
    "pf.total_alloc": {"it": "Totale allocazione (esclusi gli importi fissi)", "en": "Total allocation (excluding fixed amounts)", "es": "Asignación total (excluyendo importes fijos)", "fr": "Allocation totale (hors montants fixes)", "de": "Gesamtallokation (ohne feste Beträge)", "uk": "Загальний розподіл (без фіксованих сум)"},
    "th.price": {"it": "Prezzo", "en": "Price", "es": "Precio", "fr": "Prix", "de": "Kurs", "uk": "Ціна"},
    "pf.unavailable": {"it": "non disponibile", "en": "unavailable", "es": "no disponible", "fr": "indisponible", "de": "nicht verfügbar", "uk": "недоступно"},
    "pf.btn_refresh": {"it": "Aggiorna prezzi", "en": "Refresh prices", "es": "Actualizar precios", "fr": "Actualiser les prix", "de": "Kurse aktualisieren", "uk": "Оновити ціни"},
    "pf.total_value": {"it": "Valore totale del portafoglio", "en": "Total portfolio value", "es": "Valor total de la cartera", "fr": "Valeur totale du portefeuille", "de": "Gesamtwert des Portfolios", "uk": "Загальна вартість портфеля"},
    "pf.prices_updated": {"it": "Prezzi aggiornati: {when}", "en": "Prices updated: {when}", "es": "Precios actualizados: {when}", "fr": "Prix mis à jour : {when}", "de": "Kurse aktualisiert: {when}", "uk": "Ціни оновлено: {when}"},
    "pf.prices_never": {"it": "prezzi non ancora scaricati", "en": "prices not downloaded yet", "es": "precios aún no descargados", "fr": "prix pas encore téléchargés", "de": "Kurse noch nicht geladen", "uk": "ціни ще не завантажено"},
    "pf.prices_coverage": {"it": "{n}/{tot} prezzi disponibili", "en": "{n}/{tot} prices available", "es": "{n}/{tot} precios disponibles", "fr": "{n}/{tot} prix disponibles", "de": "{n}/{tot} Kurse verfügbar", "uk": "{n}/{tot} цін доступно"},
    "pf.prices_note": {"it": "Prezzi pubblici da Yahoo Finance, aggiornati all'apertura. Valore = quantità × prezzo, dove hai inserito la quantità. Dato non reperibile: «non disponibile», mai inventato.", "en": "Public prices from Yahoo Finance, refreshed on launch. Value = quantity × price, where you entered a quantity. Missing data: «unavailable», never made up.", "es": "Precios públicos de Yahoo Finance, actualizados al abrir. Valor = cantidad × precio, donde hayas introducido la cantidad. Dato no disponible: «no disponible», nunca inventado.", "fr": "Prix publics de Yahoo Finance, actualisés au lancement. Valeur = quantité × prix, là où tu as saisi une quantité. Donnée manquante : « indisponible », jamais inventée.", "de": "Öffentliche Kurse von Yahoo Finance, beim Start aktualisiert. Wert = Menge × Kurs, sofern du eine Menge eingegeben hast. Fehlende Daten: «nicht verfügbar», nie erfunden.", "uk": "Публічні ціни з Yahoo Finance, оновлюються при запуску. Вартість = кількість × ціна, де ти ввів кількість. Відсутні дані: «недоступно», ніколи не вигадані."},
    "dash.stat_pf_value": {"it": "Valore del portafoglio", "en": "Portfolio value", "es": "Valor de la cartera", "fr": "Valeur du portefeuille", "de": "Portfoliowert", "uk": "Вартість портфеля"},
    "dash.value_live": {"it": "da prezzi correnti, dove hai messo le quantità", "en": "from current prices, where you set quantities", "es": "según precios actuales, donde pusiste cantidades", "fr": "selon les prix actuels, où tu as mis les quantités", "de": "aus aktuellen Kursen, wo du Mengen angegeben hast", "uk": "за поточними цінами, де ти вказав кількість"},
    "pf.holdings_toggle": {"it": "Holdings", "en": "Holdings", "es": "Holdings", "fr": "Positions", "de": "Positionen", "uk": "Активи"},
    "detail.back": {"it": "← Portafoglio", "en": "← Portfolio", "es": "← Cartera", "fr": "← Portefeuille", "de": "← Portfolio", "uk": "← Портфель"},
    "detail.fund_data": {"it": "Dati di fondo", "en": "Fund data", "es": "Datos del fondo", "fr": "Données du fonds", "de": "Fondsdaten", "uk": "Дані фонду"},
    "detail.holdings": {"it": "Holdings (Top 10)", "en": "Holdings (Top 10)", "es": "Holdings (Top 10)", "fr": "Positions (Top 10)", "de": "Positionen (Top 10)", "uk": "Активи (Топ-10)"},
    "detail.holdings_partial": {"it": "Elenco parziale: le prime 10 posizioni. Le holdings complete non sono reperibili gratuitamente.", "en": "Partial list: the top 10 positions. Full holdings aren't available for free.", "es": "Lista parcial: las 10 primeras posiciones. Las holdings completas no están disponibles gratis.", "fr": "Liste partielle : les 10 premières positions. Les positions complètes ne sont pas disponibles gratuitement.", "de": "Teilliste: die Top-10-Positionen. Vollständige Bestände sind nicht kostenlos verfügbar.", "uk": "Частковий список: топ-10 позицій. Повний склад недоступний безкоштовно."},
    "detail.sectors": {"it": "Esposizione settoriale", "en": "Sector exposure", "es": "Exposición sectorial", "fr": "Exposition sectorielle", "de": "Sektor-Engagement", "uk": "Секторний розподіл"},
    "detail.category": {"it": "Categoria", "en": "Category", "es": "Categoría", "fr": "Catégorie", "de": "Kategorie", "uk": "Категорія"},
    "detail.ter": {"it": "Costo annuo (TER)", "en": "Annual cost (TER)", "es": "Coste anual (TER)", "fr": "Coût annuel (TER)", "de": "Jährliche Kosten (TER)", "uk": "Річна комісія (TER)"},
    "detail.assets": {"it": "Patrimonio (AUM)", "en": "Assets (AUM)", "es": "Patrimonio (AUM)", "fr": "Encours (AUM)", "de": "Vermögen (AUM)", "uk": "Активи (AUM)"},
    "detail.div_yield": {"it": "Rendimento da dividendo", "en": "Dividend yield", "es": "Rentabilidad por dividendo", "fr": "Rendement du dividende", "de": "Dividendenrendite", "uk": "Дивідендна дохідність"},
    "detail.beta": {"it": "Beta (volatilità vs mercato)", "en": "Beta (volatility vs market)", "es": "Beta (volatilidad vs mercado)", "fr": "Bêta (volatilité vs marché)", "de": "Beta (Volatilität vs. Markt)", "uk": "Бета (волатильність до ринку)"},
    "detail.sector_l": {"it": "Settore", "en": "Sector", "es": "Sector", "fr": "Secteur", "de": "Sektor", "uk": "Сектор"},
    "detail.industry": {"it": "Industria", "en": "Industry", "es": "Industria", "fr": "Industrie", "de": "Branche", "uk": "Галузь"},
    "detail.country": {"it": "Paese", "en": "Country", "es": "País", "fr": "Pays", "de": "Land", "uk": "Країна"},
    "detail.weight": {"it": "Peso", "en": "Weight", "es": "Peso", "fr": "Poids", "de": "Gewicht", "uk": "Вага"},
    "detail.no_data": {"it": "Dati di dettaglio non disponibili al momento (riprova più tardi).", "en": "Detailed data not available right now (try again later).", "es": "Datos detallados no disponibles ahora (inténtalo más tarde).", "fr": "Données détaillées indisponibles pour l'instant (réessaie plus tard).", "de": "Detaildaten derzeit nicht verfügbar (später erneut versuchen).", "uk": "Детальні дані наразі недоступні (спробуй пізніше)."},
    "detail.updated": {"it": "Aggiornato: {when}", "en": "Updated: {when}", "es": "Actualizado: {when}", "fr": "Mis à jour : {when}", "de": "Aktualisiert: {when}", "uk": "Оновлено: {when}"},
    "detail.price_current": {"it": "Prezzo attuale", "en": "Current price", "es": "Precio actual", "fr": "Prix actuel", "de": "Aktueller Kurs", "uk": "Поточна ціна"},
    "detail.note": {"it": "Nota", "en": "Note", "es": "Nota", "fr": "Note", "de": "Notiz", "uk": "Примітка"},
    "nav.analisi": {"it": "Analisi", "en": "Analysis", "es": "Análisis", "fr": "Analyse", "de": "Analyse", "uk": "Аналіз"},
    "analisi.title": {"it": "Analisi & rischio", "en": "Analysis & risk", "es": "Análisis y riesgo", "fr": "Analyse et risque", "de": "Analyse & Risiko", "uk": "Аналіз і ризик"},
    "analisi.subtitle": {"it": "Fotografia descrittiva del portafoglio: dove sei esposto e quanto oscilla. Non è un consiglio.", "en": "A descriptive snapshot of the portfolio: where you're exposed and how much it swings. Not advice.", "es": "Una foto descriptiva de la cartera: dónde estás expuesto y cuánto oscila. No es un consejo.", "fr": "Un aperçu descriptif du portefeuille : où tu es exposé et combien ça bouge. Pas un conseil.", "de": "Eine beschreibende Momentaufnahme des Portfolios: wo du engagiert bist und wie stark es schwankt. Keine Beratung.", "uk": "Описовий знімок портфеля: де ти маєш експозицію і наскільки він коливається. Не порада."},
    "analisi.sector_exposure": {"it": "Esposizione settoriale (look-through)", "en": "Sector exposure (look-through)", "es": "Exposición sectorial (look-through)", "fr": "Exposition sectorielle (look-through)", "de": "Sektor-Engagement (Look-Through)", "uk": "Секторна експозиція (наскрізна)"},
    "analisi.sector_note": {"it": "ETF scomposti nei loro settori, azioni per settore, pesati sulla % target. Copertura dati: {cop}% di {tot}%.", "en": "ETFs broken into their sectors, stocks by sector, weighted by target %. Data coverage: {cop}% of {tot}%.", "es": "ETF desglosados por sectores, acciones por sector, ponderados por % objetivo. Cobertura de datos: {cop}% de {tot}%.", "fr": "ETF décomposés par secteurs, actions par secteur, pondérés par % cible. Couverture des données : {cop}% sur {tot}%.", "de": "ETFs in ihre Sektoren zerlegt, Aktien nach Sektor, gewichtet nach Ziel-%. Datenabdeckung: {cop}% von {tot}%.", "uk": "ETF розкладено за секторами, акції за сектором, зважено за цільовим %. Покриття даних: {cop}% з {tot}%."},
    "analisi.tech_conc": {"it": "Concentrazione tecnologia", "en": "Technology concentration", "es": "Concentración en tecnología", "fr": "Concentration technologie", "de": "Technologie-Konzentration", "uk": "Концентрація в технологіях"},
    "analisi.tech_alert": {"it": "⚠ Oltre il 50%: forte concentrazione sul settore tech.", "en": "⚠ Over 50%: heavy concentration in tech.", "es": "⚠ Más del 50%: fuerte concentración en tecnología.", "fr": "⚠ Plus de 50% : forte concentration sur la tech.", "de": "⚠ Über 50%: starke Konzentration im Tech-Sektor.", "uk": "⚠ Понад 50%: висока концентрація в техсекторі."},
    "analisi.tech_ok": {"it": "Sotto la soglia del 50%.", "en": "Below the 50% threshold.", "es": "Por debajo del umbral del 50%.", "fr": "Sous le seuil de 50%.", "de": "Unter der 50%-Schwelle.", "uk": "Нижче порога 50%."},
    "analisi.geo_note": {"it": "Esposizione geografica completa (USA/area): richiede i dati paese degli ETF, non gratuiti. In arrivo.", "en": "Full geographic exposure (US/region): needs ETF country data, not free. Coming later.", "es": "Exposición geográfica completa (EE.UU./región): requiere datos por país de los ETF, no gratuitos. Próximamente.", "fr": "Exposition géographique complète (USA/région) : nécessite les données pays des ETF, non gratuites. À venir.", "de": "Vollständiges geografisches Engagement (USA/Region): erfordert Länderdaten der ETFs, nicht kostenlos. Kommt später.", "uk": "Повна географічна експозиція (США/регіон): потребує країнових даних ETF, не безкоштовних. Згодом."},
    "analisi.div_yield": {"it": "Rendimento da dividendo (stimato)", "en": "Dividend yield (estimated)", "es": "Rentabilidad por dividendo (estimada)", "fr": "Rendement du dividende (estimé)", "de": "Dividendenrendite (geschätzt)", "uk": "Дивідендна дохідність (оцінка)"},
    "analisi.diversification": {"it": "Diversificazione (titoli equivalenti)", "en": "Diversification (effective holdings)", "es": "Diversificación (posiciones efectivas)", "fr": "Diversification (positions effectives)", "de": "Diversifikation (effektive Positionen)", "uk": "Диверсифікація (ефективні позиції)"},
    "analisi.div_hint": {"it": "Numero 'effettivo' di posizioni viste le tue %: più alto = più diversificato.", "en": "'Effective' number of positions given your %: higher = more diversified.", "es": "Número 'efectivo' de posiciones según tus %: más alto = más diversificado.", "fr": "Nombre 'effectif' de positions selon tes % : plus élevé = plus diversifié.", "de": "'Effektive' Anzahl Positionen gemäß deinen %: höher = stärker diversifiziert.", "uk": "'Ефективна' кількість позицій за твоїми %: більше = більш диверсифіковано."},
    "analisi.risk_h": {"it": "Metriche di rischio (ultimo anno)", "en": "Risk metrics (last year)", "es": "Métricas de riesgo (último año)", "fr": "Mesures de risque (1 an)", "de": "Risikokennzahlen (letztes Jahr)", "uk": "Метрики ризику (рік)"},
    "analisi.risk_note": {"it": "Calcolo pesante su dati settimanali: premi per calcolarle o aggiornarle (qualche secondo).", "en": "Heavy calculation on weekly data: press to compute or refresh (a few seconds).", "es": "Cálculo pesado sobre datos semanales: pulsa para calcular o actualizar (unos segundos).", "fr": "Calcul lourd sur données hebdomadaires : appuie pour calculer ou actualiser (quelques secondes).", "de": "Aufwändige Berechnung auf Wochendaten: drücke zum Berechnen/Aktualisieren (ein paar Sekunden).", "uk": "Важкий розрахунок на тижневих даних: натисни, щоб обчислити або оновити (кілька секунд)."},
    "analisi.btn_compute": {"it": "Calcola metriche di rischio", "en": "Compute risk metrics", "es": "Calcular métricas de riesgo", "fr": "Calculer les mesures de risque", "de": "Risikokennzahlen berechnen", "uk": "Обчислити метрики ризику"},
    "analisi.btn_recompute": {"it": "Ricalcola", "en": "Recompute", "es": "Recalcular", "fr": "Recalculer", "de": "Neu berechnen", "uk": "Перерахувати"},
    "analisi.vol": {"it": "Volatilità annua", "en": "Annual volatility", "es": "Volatilidad anual", "fr": "Volatilité annuelle", "de": "Jährliche Volatilität", "uk": "Річна волатильність"},
    "analisi.vol_hint": {"it": "Quanto oscilla il portafoglio: più alta = più ballerino.", "en": "How much the portfolio swings: higher = bumpier.", "es": "Cuánto oscila la cartera: más alta = más movida.", "fr": "Combien le portefeuille bouge : plus élevé = plus agité.", "de": "Wie stark das Portfolio schwankt: höher = unruhiger.", "uk": "Наскільки коливається портфель: більше = тряскіше."},
    "analisi.mdd": {"it": "Massima discesa (drawdown)", "en": "Maximum drawdown", "es": "Máxima caída (drawdown)", "fr": "Perte maximale (drawdown)", "de": "Maximaler Drawdown", "uk": "Максимальна просадка"},
    "analisi.mdd_hint": {"it": "La peggior caduta dal picco nell'ultimo anno.", "en": "The worst drop from a peak in the last year.", "es": "La peor caída desde un máximo en el último año.", "fr": "La pire chute depuis un pic sur l'année.", "de": "Der schlimmste Rückgang von einem Hoch im letzten Jahr.", "uk": "Найгірше падіння від піку за рік."},
    "analisi.sharpe": {"it": "Sharpe ratio", "en": "Sharpe ratio", "es": "Ratio de Sharpe", "fr": "Ratio de Sharpe", "de": "Sharpe-Ratio", "uk": "Коефіцієнт Шарпа"},
    "analisi.sharpe_hint": {"it": "Rendimento per unità di rischio: più alto è meglio.", "en": "Return per unit of risk: higher is better.", "es": "Rentabilidad por unidad de riesgo: más alto es mejor.", "fr": "Rendement par unité de risque : plus c'est élevé, mieux c'est.", "de": "Rendite je Risikoeinheit: höher ist besser.", "uk": "Дохід на одиницю ризику: більше — краще."},
    "analisi.beta": {"it": "Beta vs MSCI World", "en": "Beta vs MSCI World", "es": "Beta vs MSCI World", "fr": "Bêta vs MSCI World", "de": "Beta vs. MSCI World", "uk": "Бета до MSCI World"},
    "analisi.beta_hint": {"it": "1 = si muove come il mercato; >1 amplifica, <1 attenua.", "en": "1 = moves with the market; >1 amplifies, <1 dampens.", "es": "1 = se mueve como el mercado; >1 amplifica, <1 amortigua.", "fr": "1 = bouge comme le marché ; >1 amplifie, <1 atténue.", "de": "1 = bewegt sich wie der Markt; >1 verstärkt, <1 dämpft.", "uk": "1 = рухається з ринком; >1 підсилює, <1 пом'якшує."},
    "analisi.risk_meta": {"it": "Su {n} titoli, {weeks} settimane · {when}", "en": "On {n} holdings, {weeks} weeks · {when}", "es": "Sobre {n} posiciones, {weeks} semanas · {when}", "fr": "Sur {n} positions, {weeks} semaines · {when}", "de": "Auf {n} Positionen, {weeks} Wochen · {when}", "uk": "На {n} позиціях, {weeks} тижнів · {when}"},
    "analisi.risk_none": {"it": "Metriche non ancora calcolate.", "en": "Metrics not computed yet.", "es": "Métricas aún no calculadas.", "fr": "Mesures pas encore calculées.", "de": "Kennzahlen noch nicht berechnet.", "uk": "Метрики ще не обчислено."},
    "analisi.ai_descr": {"it": "Analisi automatica e descrittiva, non un consiglio finanziario.", "en": "Automatic, descriptive analysis, not financial advice.", "es": "Análisis automático y descriptivo, no asesoramiento financiero.", "fr": "Analyse automatique et descriptive, pas un conseil financier.", "de": "Automatische, beschreibende Analyse, keine Finanzberatung.", "uk": "Автоматичний описовий аналіз, не фінансова порада."},

    # ---- modulo posizione ----
    "form.title_new": {"it": "Nuova posizione", "en": "New position", "es": "Nueva posición", "fr": "Nouvelle position", "de": "Neue Position", "uk": "Нова позиція"},
    "form.title_edit": {"it": "Modifica posizione", "en": "Edit position", "es": "Editar posición", "fr": "Modifier la position", "de": "Position bearbeiten", "uk": "Редагувати позицію"},
    "form.sub_new": {"it": "Aggiungi un titolo al portafoglio.", "en": "Add a security to your portfolio.", "es": "Añade un título a tu cartera.", "fr": "Ajoute un titre à ton portefeuille.", "de": "Füge deinem Portfolio ein Wertpapier hinzu.", "uk": "Додай цінний папір до портфеля."},
    "form.sub_edit": {"it": "Stai modificando «{name}».", "en": "You're editing «{name}».", "es": "Estás editando «{name}».", "fr": "Tu modifies « {name} ».", "de": "Du bearbeitest «{name}».", "uk": "Ти редагуєш «{name}»."},
    "form.name": {"it": "Nome del titolo *", "en": "Security name *", "es": "Nombre del título *", "fr": "Nom du titre *", "de": "Wertpapiername *", "uk": "Назва паперу *"},
    "form.ph_name": {"it": "es. iShares Core MSCI World UCITS ETF", "en": "e.g. iShares Core MSCI World UCITS ETF", "es": "p. ej. iShares Core MSCI World UCITS ETF", "fr": "ex. iShares Core MSCI World UCITS ETF", "de": "z. B. iShares Core MSCI World UCITS ETF", "uk": "напр. iShares Core MSCI World UCITS ETF"},
    "form.type": {"it": "Tipo", "en": "Type", "es": "Tipo", "fr": "Type", "de": "Typ", "uk": "Тип"},
    "form.ticker": {"it": "Ticker", "en": "Ticker", "es": "Ticker", "fr": "Ticker", "de": "Ticker", "uk": "Тикер"},
    "form.isin": {"it": "ISIN", "en": "ISIN", "es": "ISIN", "fr": "ISIN", "de": "ISIN", "uk": "ISIN"},
    "form.ph_category": {"it": "es. Azionario globale, Semiconduttori, Difesa…", "en": "e.g. Global equity, Semiconductors, Defense…", "es": "p. ej. Renta variable global, Semiconductores, Defensa…", "fr": "ex. Actions monde, Semi-conducteurs, Défense…", "de": "z. B. Globale Aktien, Halbleiter, Verteidigung…", "uk": "напр. Світові акції, Напівпровідники, Оборона…"},
    "form.hint_pct": {"it": "Quota obiettivo nel portafoglio. La somma di tutte dovrebbe fare 100%.", "en": "Target weight in the portfolio. All weights should add up to 100%.", "es": "Peso objetivo en la cartera. La suma de todos debería ser 100%.", "fr": "Pondération cible dans le portefeuille. Le total devrait faire 100%.", "de": "Zielgewicht im Portfolio. Die Summe aller sollte 100% ergeben.", "uk": "Цільова вага в портфелі. Сума всіх має бути 100%."},
    "form.fixed": {"it": "Importo fisso mensile (€) — opzionale", "en": "Fixed monthly amount (€) — optional", "es": "Importe fijo mensual (€) — opcional", "fr": "Montant mensuel fixe (€) — facultatif", "de": "Fester Monatsbetrag (€) — optional", "uk": "Фіксована щомісячна сума (€) — необов'язково"},
    "form.hint_fixed": {"it": "Solo per titoli a importo fisso (es. Take-Two 1€/mese). Lascia vuoto altrimenti.", "en": "Only for fixed-amount holdings (e.g. Take-Two €1/month). Leave blank otherwise.", "es": "Solo para títulos de importe fijo (p. ej. Take-Two 1€/mes). Déjalo vacío si no.", "fr": "Uniquement pour les titres à montant fixe (ex. Take-Two 1€/mois). Sinon, laisse vide.", "de": "Nur für Positionen mit festem Betrag (z. B. Take-Two 1€/Monat). Sonst leer lassen.", "uk": "Лише для паперів із фіксованою сумою (напр. Take-Two 1€/міс). Інакше залиш порожнім."},
    "form.qty": {"it": "Quantità posseduta", "en": "Quantity held", "es": "Cantidad poseída", "fr": "Quantité détenue", "de": "Gehaltene Menge", "uk": "Кількість в наявності"},
    "form.value": {"it": "Valore posseduto (€)", "en": "Value held (€)", "es": "Valor poseído (€)", "fr": "Valeur détenue (€)", "de": "Gehaltener Wert (€)", "uk": "Вартість активів (€)"},
    "form.last_buy": {"it": "Data ultimo acquisto", "en": "Last purchase date", "es": "Fecha de última compra", "fr": "Date du dernier achat", "de": "Datum des letzten Kaufs", "uk": "Дата останньої купівлі"},
    "form.ph_optional": {"it": "opzionale", "en": "optional", "es": "opcional", "fr": "facultatif", "de": "optional", "uk": "необов'язково"},
    "form.notes": {"it": "Note", "en": "Notes", "es": "Notas", "fr": "Notes", "de": "Notizen", "uk": "Нотатки"},
    "form.ph_notes": {"it": "appunti personali…", "en": "personal notes…", "es": "notas personales…", "fr": "notes personnelles…", "de": "persönliche Notizen…", "uk": "особисті нотатки…"},
    "form.save_edit": {"it": "Salva modifiche", "en": "Save changes", "es": "Guardar cambios", "fr": "Enregistrer", "de": "Änderungen speichern", "uk": "Зберегти зміни"},
    "form.add": {"it": "Aggiungi posizione", "en": "Add position", "es": "Añadir posición", "fr": "Ajouter la position", "de": "Position hinzufügen", "uk": "Додати позицію"},
    "form.cancel": {"it": "Annulla", "en": "Cancel", "es": "Cancelar", "fr": "Annuler", "de": "Abbrechen", "uk": "Скасувати"},

    # ---- calcolatore PAC ----
    "pac.subtitle": {"it": "Inserisci quanto vuoi versare ogni mese: l'app ripartisce l'importo fra i titoli secondo la % target. È un calcolo, non un consiglio: la decisione resta tua.", "en": "Enter how much you want to invest each month: the app splits it across securities by target %. It's a calculation, not advice: the decision is yours.", "es": "Introduce cuánto quieres aportar cada mes: la app reparte el importe entre los títulos según el % objetivo. Es un cálculo, no un consejo: la decisión es tuya.", "fr": "Indique combien tu veux investir chaque mois : l'app répartit le montant entre les titres selon le % cible. C'est un calcul, pas un conseil : la décision t'appartient.", "de": "Gib an, wie viel du monatlich investieren willst: Die App verteilt den Betrag nach Ziel-% auf die Wertpapiere. Es ist eine Berechnung, keine Beratung: Die Entscheidung liegt bei dir.", "uk": "Вкажи, скільки хочеш інвестувати щомісяця: застосунок розподілить суму між паперами за цільовим %. Це розрахунок, а не порада: рішення за тобою."},
    "pac.label_amount": {"it": "Importo mensile da investire (€)", "en": "Monthly amount to invest (€)", "es": "Importe mensual a invertir (€)", "fr": "Montant mensuel à investir (€)", "de": "Monatlicher Anlagebetrag (€)", "uk": "Щомісячна сума для інвестування (€)"},
    "pac.ph_amount": {"it": "es. 500", "en": "e.g. 500", "es": "p. ej. 500", "fr": "ex. 500", "de": "z. B. 500", "uk": "напр. 500"},
    "pac.btn_calc": {"it": "Calcola", "en": "Calculate", "es": "Calcular", "fr": "Calculer", "de": "Berechnen", "uk": "Розрахувати"},
    "pac.hint": {"it": "In futuro questo importo potrà essere suggerito dal tuo cash flow reale (Fase 3+).", "en": "In the future this amount can be suggested by your real cash flow (Phase 3+).", "es": "En el futuro este importe podrá sugerirlo tu flujo de caja real (Fase 3+).", "fr": "À l'avenir, ce montant pourra être suggéré par ton flux de trésorerie réel (Phase 3+).", "de": "Künftig kann dieser Betrag aus deinem echten Cashflow vorgeschlagen werden (Phase 3+).", "uk": "У майбутньому цю суму зможе пропонувати твій реальний грошовий потік (Фаза 3+)."},
    "pac.warn_not100": {"it": "⚠ La somma delle % target fa {pct}, non 100%. Le quote qui sotto sono comunque calcolate, ma il totale non coinciderà con l'importo finché non sistemi l'allocazione nel portafoglio.", "en": "⚠ Target % sum is {pct}, not 100%. The amounts below are still calculated, but the total won't match your input until you fix the allocation in the portfolio.", "es": "⚠ La suma de % objetivo es {pct}, no 100%. Los importes de abajo se calculan igualmente, pero el total no coincidirá con tu importe hasta que ajustes la asignación en la cartera.", "fr": "⚠ La somme des % cibles est {pct}, pas 100%. Les montants ci-dessous sont quand même calculés, mais le total ne correspondra pas tant que tu n'auras pas corrigé l'allocation dans le portefeuille.", "de": "⚠ Summe der Ziel-% beträgt {pct}, nicht 100%. Die Beträge unten werden trotzdem berechnet, aber die Summe passt erst zu deinem Betrag, wenn du die Allokation im Portfolio korrigierst.", "uk": "⚠ Сума цільових % дорівнює {pct}, а не 100%. Суми нижче все одно розраховано, але загальна сума не збігатиметься з твоєю, доки ти не виправиш розподіл у портфелі."},
    "pac.stat_invested": {"it": "Versato sui {n} asset a %", "en": "Invested across {n} % assets", "es": "Invertido en {n} activos por %", "fr": "Investi sur {n} actifs en %", "de": "Auf {n} %-Werte verteilt", "uk": "Розподілено на {n} активів за %"},
    "pac.stat_fixed": {"it": "Importi fissi (es. Take-Two)", "en": "Fixed amounts (e.g. Take-Two)", "es": "Importes fijos (p. ej. Take-Two)", "fr": "Montants fixes (ex. Take-Two)", "de": "Feste Beträge (z. B. Take-Two)", "uk": "Фіксовані суми (напр. Take-Two)"},
    "pac.stat_total": {"it": "Uscita mensile totale", "en": "Total monthly outflow", "es": "Salida mensual total", "fr": "Sortie mensuelle totale", "de": "Monatlicher Gesamtabfluss", "uk": "Загальний щомісячний відтік"},
    "pac.stat_total_sub": {"it": "% + importi fissi", "en": "% + fixed amounts", "es": "% + importes fijos", "fr": "% + montants fixes", "de": "% + feste Beträge", "uk": "% + фіксовані суми"},
    "pac.stat_round": {"it": "Scostamento da arrotondamenti", "en": "Rounding difference", "es": "Diferencia por redondeo", "fr": "Écart d'arrondi", "de": "Rundungsdifferenz", "uk": "Різниця через округлення"},
    "pac.stat_round_sub": {"it": "differenza coi centesimi", "en": "difference in cents", "es": "diferencia en céntimos", "fr": "différence en centimes", "de": "Differenz in Cent", "uk": "різниця в центах"},
    "pac.col_quota": {"it": "Quota mensile", "en": "Monthly amount", "es": "Cuota mensual", "fr": "Montant mensuel", "de": "Monatsbetrag", "uk": "Щомісячна сума"},
    "pac.implicit": {"it": "(implicita)", "en": "(implied)", "es": "(implícita)", "fr": "(implicite)", "de": "(implizit)", "uk": "(неявно)"},
    "pac.fixed_badge": {"it": "importo fisso", "en": "fixed amount", "es": "importe fijo", "fr": "montant fixe", "de": "fester Betrag", "uk": "фіксована сума"},

    # ---- impostazioni ----
    "set.subtitle": {"it": "Chiavi API per sbloccare funzioni extra. L'app funziona anche senza: le chiavi restano solo sul tuo PC e non finiscono mai su GitHub.", "en": "API keys to unlock extra features. The app works without them too: keys stay only on your PC and never go to GitHub.", "es": "Claves API para desbloquear funciones extra. La app funciona también sin ellas: las claves se quedan solo en tu PC y nunca van a GitHub.", "fr": "Clés API pour débloquer des fonctions supplémentaires. L'app fonctionne aussi sans : les clés restent uniquement sur ton PC et ne vont jamais sur GitHub.", "de": "API-Schlüssel zum Freischalten zusätzlicher Funktionen. Die App funktioniert auch ohne: Schlüssel bleiben nur auf deinem PC und gelangen nie zu GitHub.", "uk": "API-ключі для розблокування додаткових функцій. Застосунок працює й без них: ключі залишаються лише на твоєму ПК і ніколи не потрапляють на GitHub."},
    "set.saved": {"it": "✓ Impostazioni salvate.", "en": "✓ Settings saved.", "es": "✓ Ajustes guardados.", "fr": "✓ Paramètres enregistrés.", "de": "✓ Einstellungen gespeichert.", "uk": "✓ Налаштування збережено."},
    "set.security_note": {"it": "🔒 Le chiavi sono salvate nel database locale (app/data/finanza.db), escluso dal backup online. Non vengono mai mostrate in chiaro né registrate nei log. Per ora nessuna è obbligatoria.", "en": "🔒 Keys are stored in the local database (app/data/finanza.db), excluded from online backup. They're never shown in clear text or written to logs. None are required for now.", "es": "🔒 Las claves se guardan en la base de datos local (app/data/finanza.db), excluida del backup online. Nunca se muestran en claro ni se registran en los logs. Por ahora ninguna es obligatoria.", "fr": "🔒 Les clés sont stockées dans la base locale (app/data/finanza.db), exclue de la sauvegarde en ligne. Elles ne sont jamais affichées en clair ni écrites dans les journaux. Aucune n'est requise pour l'instant.", "de": "🔒 Die Schlüssel werden in der lokalen Datenbank (app/data/finanza.db) gespeichert und vom Online-Backup ausgeschlossen. Sie werden nie im Klartext angezeigt oder protokolliert. Derzeit ist keiner erforderlich.", "uk": "🔒 Ключі зберігаються в локальній базі (app/data/finanza.db), виключеній з онлайн-резервування. Вони ніколи не показуються відкрито й не пишуться в логи. Наразі жоден не обов'язковий."},
    "set.current": {"it": "Attuale: {masked} · presente ✓", "en": "Current: {masked} · present ✓", "es": "Actual: {masked} · presente ✓", "fr": "Actuel : {masked} · présent ✓", "de": "Aktuell: {masked} · vorhanden ✓", "uk": "Поточний: {masked} · присутній ✓"},
    "set.ph_keep": {"it": "lascia vuoto per non modificarla", "en": "leave blank to keep it", "es": "déjalo vacío para no cambiarla", "fr": "laisse vide pour ne pas la changer", "de": "leer lassen, um ihn zu behalten", "uk": "залиш порожнім, щоб не змінювати"},
    "set.ph_new": {"it": "incolla qui la chiave", "en": "paste the key here", "es": "pega aquí la clave", "fr": "colle la clé ici", "de": "Schlüssel hier einfügen", "uk": "встав ключ сюди"},
    "set.remove_key": {"it": "rimuovi questa chiave", "en": "remove this key", "es": "eliminar esta clave", "fr": "supprimer cette clé", "de": "diesen Schlüssel entfernen", "uk": "видалити цей ключ"},
    "set.save": {"it": "Salva", "en": "Save", "es": "Guardar", "fr": "Enregistrer", "de": "Speichern", "uk": "Зберегти"},
    "set.back_dashboard": {"it": "Torna alla dashboard", "en": "Back to dashboard", "es": "Volver al panel", "fr": "Retour au tableau de bord", "de": "Zurück zur Übersicht", "uk": "Назад до панелі"},
    "set.what_h": {"it": "A cosa servono", "en": "What they're for", "es": "Para qué sirven", "fr": "À quoi elles servent", "de": "Wofür sie sind", "uk": "Для чого вони"},
    "set.gemini_for": {"it": "Gemini (gratis su aistudio.google.com): attiverà l'agente AI — Fase 4.", "en": "Gemini (free at aistudio.google.com): will power the AI assistant — Phase 4.", "es": "Gemini (gratis en aistudio.google.com): activará el asistente IA — Fase 4.", "fr": "Gemini (gratuit sur aistudio.google.com) : activera l'assistant IA — Phase 4.", "de": "Gemini (kostenlos auf aistudio.google.com): aktiviert den KI-Assistenten — Phase 4.", "uk": "Gemini (безкоштовно на aistudio.google.com): активує ШІ-помічника — Фаза 4."},
    "set.finnhub_for": {"it": "Finnhub (free tier): notizie e giudizi degli analisti — Fase 2.", "en": "Finnhub (free tier): news and analyst ratings — Phase 2.", "es": "Finnhub (plan gratuito): noticias y valoraciones de analistas — Fase 2.", "fr": "Finnhub (offre gratuite) : actualités et avis d'analystes — Phase 2.", "de": "Finnhub (kostenlose Stufe): Nachrichten und Analystenbewertungen — Phase 2.", "uk": "Finnhub (безкоштовний тариф): новини та оцінки аналітиків — Фаза 2."},
    "set.fmp_for": {"it": "Financial Modeling Prep: dati avanzati opzionali — più avanti.", "en": "Financial Modeling Prep: optional advanced data — later.", "es": "Financial Modeling Prep: datos avanzados opcionales — más adelante.", "fr": "Financial Modeling Prep : données avancées en option — plus tard.", "de": "Financial Modeling Prep: optionale erweiterte Daten — später.", "uk": "Financial Modeling Prep: додаткові розширені дані — згодом."},
    "set.appearance_h": {"it": "Aspetto e lingua", "en": "Appearance & language", "es": "Apariencia e idioma", "fr": "Apparence et langue", "de": "Darstellung & Sprache", "uk": "Вигляд і мова"},
    "set.theme_label": {"it": "Tema", "en": "Theme", "es": "Tema", "fr": "Thème", "de": "Theme", "uk": "Тема"},
    "set.apply": {"it": "Applica", "en": "Apply", "es": "Aplicar", "fr": "Appliquer", "de": "Anwenden", "uk": "Застосувати"},
    "set.key_gemini": {"it": "Chiave API Google Gemini (agente AI)", "en": "Google Gemini API key (AI assistant)", "es": "Clave API de Google Gemini (asistente IA)", "fr": "Clé API Google Gemini (assistant IA)", "de": "Google-Gemini-API-Schlüssel (KI-Assistent)", "uk": "API-ключ Google Gemini (ШІ-помічник)"},
    "set.key_finnhub": {"it": "Chiave API Finnhub (notizie/analisti)", "en": "Finnhub API key (news/analysts)", "es": "Clave API de Finnhub (noticias/analistas)", "fr": "Clé API Finnhub (actualités/analystes)", "de": "Finnhub-API-Schlüssel (Nachrichten/Analysten)", "uk": "API-ключ Finnhub (новини/аналітики)"},
    "set.key_fmp": {"it": "Chiave API Financial Modeling Prep", "en": "Financial Modeling Prep API key", "es": "Clave API de Financial Modeling Prep", "fr": "Clé API Financial Modeling Prep", "de": "Financial-Modeling-Prep-API-Schlüssel", "uk": "API-ключ Financial Modeling Prep"},
}

# Categorie/temi precaricati da noi: tradotti (chiave = etichetta salvata nel DB).
# Le categorie che crei TU a mano non sono qui: restano come le scrivi.
CATEGORIES = {
    "Azionario globale": {"it": "Azionario globale", "en": "Global equity", "es": "Renta variable global", "fr": "Actions monde", "de": "Globale Aktien", "uk": "Світові акції"},
    "Azionario USA": {"it": "Azionario USA", "en": "US equity", "es": "Renta variable EE. UU.", "fr": "Actions USA", "de": "US-Aktien", "uk": "Акції США"},
    "Tech USA": {"it": "Tech USA", "en": "US tech", "es": "Tecnología EE. UU.", "fr": "Tech USA", "de": "US-Technologie", "uk": "Технології США"},
    "Dividendi globali": {"it": "Dividendi globali", "en": "Global dividends", "es": "Dividendos globales", "fr": "Dividendes monde", "de": "Globale Dividenden", "uk": "Світові дивіденди"},
    "Sanita'": {"it": "Sanità", "en": "Healthcare", "es": "Salud", "fr": "Santé", "de": "Gesundheit", "uk": "Охорона здоров'я"},
    "Difesa": {"it": "Difesa", "en": "Defense", "es": "Defensa", "fr": "Défense", "de": "Verteidigung", "uk": "Оборона"},
    "Nucleare & uranio": {"it": "Nucleare & uranio", "en": "Nuclear & uranium", "es": "Nuclear y uranio", "fr": "Nucléaire & uranium", "de": "Kernkraft & Uran", "uk": "Атом і уран"},
    "Materiali": {"it": "Materiali", "en": "Materials", "es": "Materiales", "fr": "Matériaux", "de": "Rohstoffe", "uk": "Матеріали"},
    "Infrastrutture": {"it": "Infrastrutture", "en": "Infrastructure", "es": "Infraestructura", "fr": "Infrastructure", "de": "Infrastruktur", "uk": "Інфраструктура"},
    "Ricostruzione Ucraina": {"it": "Ricostruzione Ucraina", "en": "Ukraine reconstruction", "es": "Reconstrucción de Ucrania", "fr": "Reconstruction de l'Ukraine", "de": "Wiederaufbau Ukraine", "uk": "Відбудова України"},
    "Innovazione sanitaria": {"it": "Innovazione sanitaria", "en": "Healthcare innovation", "es": "Innovación sanitaria", "fr": "Innovation santé", "de": "Gesundheitsinnovation", "uk": "Інновації в медицині"},
    "Semiconduttori": {"it": "Semiconduttori", "en": "Semiconductors", "es": "Semiconductores", "fr": "Semi-conducteurs", "de": "Halbleiter", "uk": "Напівпровідники"},
    "Spazio & difesa": {"it": "Spazio & difesa", "en": "Space & defense", "es": "Espacio y defensa", "fr": "Espace & défense", "de": "Raumfahrt & Verteidigung", "uk": "Космос і оборона"},
    "Semiconduttori / AI": {"it": "Semiconduttori / AI", "en": "Semiconductors / AI", "es": "Semiconductores / IA", "fr": "Semi-conducteurs / IA", "de": "Halbleiter / KI", "uk": "Напівпровідники / ШІ"},
    "Tech / Cloud": {"it": "Tech / Cloud", "en": "Tech / Cloud", "es": "Tecnología / Nube", "fr": "Tech / Cloud", "de": "Tech / Cloud", "uk": "Технології / Хмара"},
    "Tech / Internet": {"it": "Tech / Internet", "en": "Tech / Internet", "es": "Tecnología / Internet", "fr": "Tech / Internet", "de": "Tech / Internet", "uk": "Технології / Інтернет"},
    "Hardware / Storage": {"it": "Hardware / Storage", "en": "Hardware / Storage", "es": "Hardware / Almacenamiento", "fr": "Matériel / Stockage", "de": "Hardware / Speicher", "uk": "Обладнання / Сховище"},
    "Tech / Hardware": {"it": "Tech / Hardware", "en": "Tech / Hardware", "es": "Tecnología / Hardware", "fr": "Tech / Matériel", "de": "Tech / Hardware", "uk": "Технології / Обладнання"},
    "Software / AI": {"it": "Software / AI", "en": "Software / AI", "es": "Software / IA", "fr": "Logiciel / IA", "de": "Software / KI", "uk": "ПЗ / ШІ"},
    "Finanza / Banche": {"it": "Finanza / Banche", "en": "Finance / Banks", "es": "Finanzas / Bancos", "fr": "Finance / Banques", "de": "Finanzen / Banken", "uk": "Фінанси / Банки"},
    "Farmaceutica": {"it": "Farmaceutica", "en": "Pharmaceuticals", "es": "Farmacéutica", "fr": "Pharmaceutique", "de": "Pharma", "uk": "Фармацевтика"},
    "Farmaceutica / Biotech": {"it": "Farmaceutica / Biotech", "en": "Pharma / Biotech", "es": "Farma / Biotech", "fr": "Pharma / Biotech", "de": "Pharma / Biotech", "uk": "Фарма / Біотех"},
    "Tech / E-commerce": {"it": "Tech / E-commerce", "en": "Tech / E-commerce", "es": "Tecnología / Comercio electrónico", "fr": "Tech / E-commerce", "de": "Tech / E-Commerce", "uk": "Технології / Електронна комерція"},
    "Tech / Social": {"it": "Tech / Social", "en": "Tech / Social", "es": "Tecnología / Redes sociales", "fr": "Tech / Réseaux sociaux", "de": "Tech / Soziale Medien", "uk": "Технології / Соцмережі"},
    "Retail / Consumi": {"it": "Retail / Consumi", "en": "Retail / Consumer", "es": "Comercio / Consumo", "fr": "Distribution / Consommation", "de": "Einzelhandel / Konsum", "uk": "Роздріб / Споживання"},
    "Media / Streaming": {"it": "Media / Streaming", "en": "Media / Streaming", "es": "Medios / Streaming", "fr": "Médias / Streaming", "de": "Medien / Streaming", "uk": "Медіа / Стримінг"},
    "Beni di consumo": {"it": "Beni di consumo", "en": "Consumer goods", "es": "Bienes de consumo", "fr": "Biens de consommation", "de": "Konsumgüter", "uk": "Споживчі товари"},
    "Energia": {"it": "Energia", "en": "Energy", "es": "Energía", "fr": "Énergie", "de": "Energie", "uk": "Енергетика"},
    "Farmaceutica / Salute": {"it": "Farmaceutica / Salute", "en": "Pharma / Health", "es": "Farma / Salud", "fr": "Pharma / Santé", "de": "Pharma / Gesundheit", "uk": "Фарма / Здоров'я"},
    "Industriale": {"it": "Industriale", "en": "Industrial", "es": "Industrial", "fr": "Industrie", "de": "Industrie", "uk": "Промисловість"},
    "Gaming / Media": {"it": "Gaming / Media", "en": "Gaming / Media", "es": "Videojuegos / Medios", "fr": "Jeux vidéo / Médias", "de": "Gaming / Medien", "uk": "Ігри / Медіа"},
}


# Settori GICS come li nomina Yahoo -> etichette leggibili e tradotte.
SECTORS = {
    "realestate": {"it": "Immobiliare", "en": "Real estate", "es": "Inmobiliario", "fr": "Immobilier", "de": "Immobilien", "uk": "Нерухомість"},
    "consumer_cyclical": {"it": "Consumi ciclici", "en": "Consumer cyclical", "es": "Consumo cíclico", "fr": "Consommation cyclique", "de": "Zyklische Konsumgüter", "uk": "Циклічні товари"},
    "basic_materials": {"it": "Materiali di base", "en": "Basic materials", "es": "Materiales básicos", "fr": "Matériaux de base", "de": "Grundstoffe", "uk": "Базові матеріали"},
    "consumer_defensive": {"it": "Consumi difensivi", "en": "Consumer defensive", "es": "Consumo defensivo", "fr": "Consommation défensive", "de": "Defensive Konsumgüter", "uk": "Захисні товари"},
    "technology": {"it": "Tecnologia", "en": "Technology", "es": "Tecnología", "fr": "Technologie", "de": "Technologie", "uk": "Технології"},
    "communication_services": {"it": "Comunicazioni", "en": "Communication services", "es": "Comunicaciones", "fr": "Communications", "de": "Kommunikation", "uk": "Комунікації"},
    "financial_services": {"it": "Finanza", "en": "Financial services", "es": "Servicios financieros", "fr": "Services financiers", "de": "Finanzdienstleistungen", "uk": "Фінанси"},
    "utilities": {"it": "Utility", "en": "Utilities", "es": "Servicios públicos", "fr": "Services aux collectivités", "de": "Versorger", "uk": "Комунальні послуги"},
    "industrials": {"it": "Industriali", "en": "Industrials", "es": "Industriales", "fr": "Industrie", "de": "Industrie", "uk": "Промисловість"},
    "energy": {"it": "Energia", "en": "Energy", "es": "Energía", "fr": "Énergie", "de": "Energie", "uk": "Енергетика"},
    "healthcare": {"it": "Sanità", "en": "Healthcare", "es": "Salud", "fr": "Santé", "de": "Gesundheit", "uk": "Охорона здоров'я"},
}


def t(key: str, lang: str = DEFAULT_LANG, **kw) -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key  # chiave mancante: la mostro così è facile scovarla
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kw:
        try:
            text = text.format(**kw)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def translate_category(label: str, lang: str = DEFAULT_LANG) -> str:
    entry = CATEGORIES.get((label or "").strip())
    if not entry:
        return label or ""   # categoria tua: lasciala com'è
    return entry.get(lang) or entry.get(DEFAULT_LANG) or label


def translate_sector(key: str, lang: str = DEFAULT_LANG) -> str:
    entry = SECTORS.get((key or "").strip().lower())
    if not entry:
        return (key or "").replace("_", " ").title()
    return entry.get(lang) or entry.get(DEFAULT_LANG) or key


def make_translator(lang: str):
    """Crea la funzione t() 'agganciata' alla lingua corrente, per i template."""
    def _t(key, **kw):
        return t(key, lang, **kw)
    _t.lang = lang
    _t.category = lambda label: translate_category(label, lang)
    _t.sector = lambda key: translate_sector(key, lang)
    return _t
