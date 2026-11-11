# Chrome Web Store listing: Reclaim (v1.0.0)

Everything below is meant to be checked against manifest.json, config.js, background.js, README.md, PRIVACY.md and docs/privacy.html before submitting. Character counts are stated next to each limited field. Copy only what is inside the code blocks.

---

## 1. Name and short description (shipped inside the package)

The store takes the item name (limit 75) and short summary (limit 132) from the package's `_locales/<locale>/messages.json` (`extName`, `extDescription`, referenced from manifest.json as `__MSG_extName__` and `__MSG_extDescription__`). Do NOT paste them in the dashboard. Exact strings and character counts:

| Locale | Name | Chars | Summary | Chars |
|---|---|---|---|---|
| en | Reclaim – Stop Doomscrolling & Limit Social Media | 49 | A calm pause before time-wasting sites. Set an intention, take a few minutes, and see the time you reclaimed. | 109 |
| ro | Reclaim – Oprește doomscrollingul și limitează rețelele sociale | 63 | O pauză liniștită înainte de site-urile care îți fură timpul. Fixează-ți o intenție, ia câteva minute și vezi timpul recuperat. | 127 |
| de | Reclaim – Doomscrolling stoppen & Social Media begrenzen | 56 | Eine ruhige Pause vor Zeitfressern im Netz. Setze eine Absicht, nimm dir ein paar Minuten und sieh, wie viel Zeit du zurückgewinnst. | 132 |
| fr | Reclaim – Stop au doomscrolling et aux réseaux sociaux | 54 | Une pause calme avant les sites qui font perdre du temps. Fixez une intention, prenez quelques minutes et voyez le temps regagné. | 129 |
| es | Reclaim – Frena el doomscrolling y limita las redes sociales | 60 | Una pausa tranquila antes de los sitios que te roban tiempo. Fija una intención, tómate unos minutos y mira el tiempo recuperado. | 129 |

## 2. Rules for the public descriptions

Do not name sites, brands or consent-platform vendors in any language's public description or summary. The Chrome Web Store flagged that as keyword spam for the sister extension Wait 24h (violation 'Yellow Argon', Nov 2026). Brand and site names are fine in the reviewer notes and permission justifications only. Reclaim's public text contains none (checked by script: 0 brand names in every summary and description block).

## 3. Detailed description (EN)

```
Reclaim helps you stop doomscrolling with a calm pause before time-wasting sites. Open a popular social or video site and a quiet screen asks what you are here for. Take a few seconds, set an intention, then choose to go in or leave. You see how much time you reclaimed, and a small plant in the popup grows as your weeks go well.

HOW IT WORKS
• A calm full-screen pause appears before the page is usable. Playing media is paused until you choose.
• Optional: write what you are here for (up to 140 characters). It stays on your device and is deleted after 7 days.
• Choose "Go in" for a timed session (10 minutes by default, 5 to 30 in Options), or "Leave".
• When the session ends, a soft reminder offers "Stay 5 more" or "Leave".
• "Time reclaimed" is an estimate: each time you leave, an average session length (15 minutes by default, adjustable) is added. It is labelled as an estimate everywhere.
• Popup: time spent today, a 7-day chart, a weekly summary and a plant that reflects your week, without guilt text. Pause Reclaim for an hour whenever you need to.
• Share: copy a short text about the time you reclaimed, with a link to the extension.

WHERE IT WORKS
A built-in set of popular social and video sites (the short-video section of one of them is limited to its own pages). Add or remove sites in Options; for a site you add, Chrome asks for your permission first. Reclaim is an independent project and is not affiliated with any site.

PRIVACY
• Everything stays on your device, in your browser's local extension storage.
• No ads, no tracking, no analytics, no accounts, and no network requests by the extension.
• Four permissions: storage, tabs, alarms and scripting. Access only to the sites on your list.

OPTIONAL SUPPORT
Reclaim is free and built by one developer. If it helps, you can support it with a one-time payment (€3, €5, €10 or an amount you pick) through Stripe. The ask appears in the popup only at milestones (5, 20, 50 and 100 hours reclaimed), at most once per milestone and 30 days apart, never right after install. Choose "Don't ask again" and it stops for good. The same links are always in Options. Payments happen on Stripe's page; the extension never sees them.

The extension's interface is in English.

Open source: https://github.com/Overcrasher/reclaim
```
Characters: 2300

---

## 4. Translations (paste per language in the dashboard)

### Detailed description (ro, Romanian)

```
Reclaim te ajută să încetezi doomscrollingul printr-o pauză liniștită înainte de site-urile care îți fură timpul. Deschizi un site popular de socializare sau video și un ecran calm te întreabă pentru ce ești aici. Iei câteva secunde, îți fixezi o intenție, apoi alegi să intri sau să pleci. Vezi cât timp ai recuperat, iar o mică plantă din fereastra extensiei crește pe măsură ce săptămânile merg bine.

CUM FUNCȚIONEAZĂ
• O pauză calmă, pe tot ecranul, apare înainte ca pagina să poată fi folosită. Conținutul media care rulează este oprit până alegi.
• Opțional: scrie pentru ce ești aici (până la 140 de caractere). Rămâne pe dispozitivul tău și se șterge după 7 zile.
• Alegi „Go in” pentru o sesiune cronometrată (10 minute implicit, între 5 și 30 în Opțiuni) sau „Leave”.
• La sfârșitul sesiunii, un memento discret îți oferă „Stay 5 more” sau „Leave”.
• „Timpul recuperat” este o estimare: de fiecare dată când pleci, se adaugă o durată medie de sesiune (15 minute implicit, ajustabilă). Peste tot este marcat ca estimare.
• Fereastra extensiei: timpul petrecut azi, un grafic pe 7 zile, un rezumat săptămânal și o plantă care reflectă săptămâna ta, fără mesaje care te fac să te simți vinovat. Poți opri Reclaim pentru o oră oricând.
• Distribuire: copiezi un text scurt despre timpul recuperat, cu un link către extensie.

UNDE FUNCȚIONEAZĂ
Un set integrat de site-uri populare de socializare și video (secțiunea de clipuri scurte a unuia dintre ele este limitată la paginile ei). Adaugi sau elimini site-uri în Opțiuni; pentru un site adăugat, Chrome îți cere mai întâi permisiunea. Reclaim este un proiect independent și nu este afiliat cu niciun site.

CONFIDENȚIALITATE
• Totul rămâne pe dispozitivul tău, în spațiul local de stocare al extensiei.
• Fără reclame, fără urmărire, fără analiză, fără conturi și fără cereri de rețea din partea extensiei.
• Patru permisiuni: storage, tabs, alarms și scripting. Acces doar la site-urile din lista ta.

SUSȚINERE OPȚIONALĂ
Reclaim este gratuită și făcută de un singur dezvoltator. Dacă ți-a fost de folos, o poți susține printr-o plată unică (3 €, 5 €, 10 € sau o sumă aleasă de tine), prin Stripe. Propunerea apare în fereastra extensiei doar la praguri (5, 20, 50 și 100 de ore recuperate), cel mult o dată pe prag, la minimum 30 de zile distanță, niciodată imediat după instalare. Cu „Don't ask again” se oprește definitiv. Aceleași linkuri sunt mereu în Opțiuni. Plata se face pe pagina Stripe; extensia nu o vede.

Interfața extensiei este în limba engleză.

Cod sursă deschis: https://github.com/Overcrasher/reclaim
```
Characters: 2580

### Detailed description (de, German)

```
Reclaim hilft dir, das Doomscrolling zu beenden: mit einer ruhigen Pause vor Zeitfressern im Netz. Öffnest du eine beliebte Social-Media- oder Videoseite, fragt dich ein ruhiger Bildschirm, wofür du hier bist. Nimm dir ein paar Sekunden, setze eine Absicht und entscheide dann, ob du hineingehst oder gehst. Du siehst, wie viel Zeit du zurückgewonnen hast, und eine kleine Pflanze im Popup wächst, wenn deine Wochen gut laufen.

SO FUNKTIONIERT ES
• Vor der Seite erscheint eine ruhige Vollbild-Pause. Laufende Medien werden angehalten, bis du dich entscheidest.
• Optional: Schreibe auf, wofür du hier bist (bis zu 140 Zeichen). Das bleibt auf deinem Gerät und wird nach 7 Tagen gelöscht.
• Wähle „Go in“ für eine zeitlich begrenzte Sitzung (standardmäßig 10 Minuten, in den Optionen 5 bis 30) oder „Leave“.
• Am Ende der Sitzung bietet eine sanfte Erinnerung „Stay 5 more“ oder „Leave“ an.
• Die „zurückgewonnene Zeit“ ist eine Schätzung: Bei jedem „Leave“ wird eine durchschnittliche Sitzungsdauer addiert (standardmäßig 15 Minuten, einstellbar). Überall als Schätzung gekennzeichnet.
• Popup: Zeit von heute, ein 7-Tage-Diagramm, eine Wochenübersicht und eine Pflanze, die deine Woche spiegelt, ohne Schuldgefühle. Pausiere Reclaim jederzeit für eine Stunde.
• Teilen: Kopiere einen kurzen Text über die zurückgewonnene Zeit, mit einem Link zur Erweiterung.

WO ES FUNKTIONIERT
Eine eingebaute Auswahl beliebter Social-Media- und Videoseiten (der Kurzvideo-Bereich einer davon ist auf seine eigenen Seiten begrenzt). Seiten fügst du in den Optionen hinzu oder entfernst sie; für eine hinzugefügte Seite fragt Chrome zuerst nach deiner Erlaubnis. Reclaim ist ein unabhängiges Projekt und mit keiner Seite verbunden.

DATENSCHUTZ
• Alles bleibt auf deinem Gerät, im lokalen Erweiterungsspeicher deines Browsers.
• Keine Werbung, kein Tracking, keine Analysen, keine Konten und keine Netzwerkanfragen der Erweiterung.
• Vier Berechtigungen: storage, tabs, alarms und scripting. Zugriff nur auf die Seiten deiner Liste.

FREIWILLIGE UNTERSTÜTZUNG
Reclaim ist kostenlos und von einem einzelnen Entwickler gebaut. Wenn sie dir hilft, kannst du sie mit einer einmaligen Zahlung unterstützen (3 €, 5 €, 10 € oder ein Betrag deiner Wahl) über Stripe. Die Bitte erscheint im Popup nur bei Meilensteinen (5, 20, 50 und 100 zurückgewonnene Stunden), höchstens einmal pro Meilenstein und mit mindestens 30 Tagen Abstand, nie direkt nach der Installation. Wähle „Don't ask again“, und sie hört für immer auf. Dieselben Links findest du immer in den Optionen. Die Zahlung läuft auf der Seite von Stripe; die Erweiterung sieht sie nie.

Die Oberfläche der Erweiterung ist auf Englisch.

Open Source: https://github.com/Overcrasher/reclaim
```
Characters: 2726

### Detailed description (fr, French)

```
Reclaim vous aide à arrêter le doomscrolling grâce à une pause calme avant les sites qui font perdre du temps. Ouvrez un site populaire de réseau social ou de vidéo : un écran tranquille vous demande pourquoi vous êtes là. Prenez quelques secondes, fixez une intention, puis choisissez d'entrer ou de partir. Vous voyez le temps regagné, et une petite plante dans la fenêtre de l'extension pousse quand vos semaines se passent bien.

COMMENT ÇA MARCHE
• Une pause calme, en plein écran, apparaît avant que la page soit utilisable. Les médias en lecture sont mis en pause jusqu'à votre choix.
• Facultatif : écrivez pourquoi vous êtes là (140 caractères maximum). Cela reste sur votre appareil et est supprimé après 7 jours.
• Choisissez « Go in » pour une session chronométrée (10 minutes par défaut, de 5 à 30 dans les Options) ou « Leave ».
• À la fin de la session, un rappel discret propose « Stay 5 more » ou « Leave ».
• Le « temps regagné » est une estimation : à chaque « Leave », une durée moyenne de session est ajoutée (15 minutes par défaut, réglable). Il est partout signalé comme estimation.
• Fenêtre de l'extension : temps passé aujourd'hui, graphique sur 7 jours, bilan hebdomadaire et une plante qui reflète votre semaine, sans message culpabilisant. Mettez Reclaim en pause une heure quand vous voulez.
• Partage : copiez un court texte sur le temps regagné, avec un lien vers l'extension.

OÙ ÇA FONCTIONNE
Une sélection intégrée de sites populaires de réseaux sociaux et de vidéo (la section vidéos courtes de l'un d'eux est limitée à ses propres pages). Ajoutez ou retirez des sites dans les Options ; pour un site ajouté, Chrome demande d'abord votre autorisation. Reclaim est un projet indépendant, sans affiliation avec aucun site.

CONFIDENTIALITÉ
• Tout reste sur votre appareil, dans le stockage local de l'extension de votre navigateur.
• Aucune publicité, aucun suivi, aucune analyse, aucun compte et aucune requête réseau de l'extension.
• Quatre autorisations : storage, tabs, alarms et scripting. Accès uniquement aux sites de votre liste.

SOUTIEN FACULTATIF
Reclaim est gratuite et conçue par un seul développeur. Si elle vous est utile, vous pouvez la soutenir par un paiement unique (3 €, 5 €, 10 € ou un montant de votre choix) via Stripe. La demande n'apparaît dans la fenêtre de l'extension qu'à certains paliers (5, 20, 50 et 100 heures regagnées), au plus une fois par palier et à 30 jours d'intervalle, jamais juste après l'installation. Choisissez « Don't ask again » et elle s'arrête définitivement. Les mêmes liens sont toujours dans les Options. Le paiement se fait sur la page de Stripe ; l'extension ne le voit jamais.

L'interface de l'extension est en anglais.

Code source ouvert: https://github.com/Overcrasher/reclaim
```
Characters: 2771

### Detailed description (es, Spanish)

```
Reclaim te ayuda a frenar el doomscrolling con una pausa tranquila antes de los sitios que te roban tiempo. Abres un sitio popular de redes sociales o vídeo y una pantalla serena te pregunta a qué vienes. Tómate unos segundos, fija una intención y elige entrar o irte. Ves cuánto tiempo has recuperado, y una pequeña planta en la ventana de la extensión crece cuando tus semanas van bien.

CÓMO FUNCIONA
• Una pausa tranquila a pantalla completa aparece antes de que la página sea utilizable. Los medios en reproducción se pausan hasta que elijas.
• Opcional: escribe a qué vienes (hasta 140 caracteres). Se queda en tu dispositivo y se borra a los 7 días.
• Elige «Go in» para una sesión con tiempo (10 minutos por defecto, de 5 a 30 en Opciones) o «Leave».
• Cuando termina la sesión, un recordatorio suave ofrece «Stay 5 more» o «Leave».
• El «tiempo recuperado» es una estimación: cada vez que te vas se suma una duración media de sesión (15 minutos por defecto, ajustable). En todas partes se indica que es una estimación.
• Ventana de la extensión: tiempo de hoy, gráfico de 7 días, resumen semanal y una planta que refleja tu semana, sin mensajes de culpa. Pausa Reclaim una hora cuando lo necesites.
• Compartir: copia un texto breve sobre el tiempo recuperado, con un enlace a la extensión.

DÓNDE FUNCIONA
Una selección integrada de sitios populares de redes sociales y vídeo (la sección de vídeos cortos de uno de ellos se limita a sus propias páginas). Añade o quita sitios en Opciones; para un sitio añadido, Chrome te pide permiso primero. Reclaim es un proyecto independiente y no está afiliado a ningún sitio.

PRIVACIDAD
• Todo se queda en tu dispositivo, en el almacenamiento local de extensiones de tu navegador.
• Sin anuncios, sin seguimiento, sin analítica, sin cuentas y sin solicitudes de red por parte de la extensión.
• Cuatro permisos: storage, tabs, alarms y scripting. Acceso solo a los sitios de tu lista.

APOYO OPCIONAL
Reclaim es gratuita y la ha creado un solo desarrollador. Si te resulta útil, puedes apoyarla con un pago único (3 €, 5 €, 10 € o un importe a tu elección) a través de Stripe. La petición aparece en la ventana de la extensión solo en ciertos hitos (5, 20, 50 y 100 horas recuperadas), como máximo una vez por hito y con 30 días de separación, nunca justo después de instalar. Elige «Don't ask again» y se detiene para siempre. Los mismos enlaces están siempre en Opciones. El pago se hace en la página de Stripe; la extensión nunca lo ve.

La interfaz de la extensión está en inglés.

Código abierto: https://github.com/Overcrasher/reclaim
```
Characters: 2591

---

## 5. Category and language

- Category: Productivity › Workflow & Planning (use Well-being if the dashboard offers it).
- Languages: English (default); Romanian (ro), German (de), French (fr) and Spanish (es) as added localized listings.

## 6. Single purpose statement (Privacy practices tab)

```
Reclaim has one purpose: to add a short, calm pause before time-wasting social and video sites so the user can set an intention and decide to go in for a limited time or leave, and to show the user an estimate of the time they reclaimed.
```

## 7. Permission justifications

### storage
```
Stores the user's settings (site list, countdown and session lengths, average session length), the daily time totals for the last 60 days, the intentions the user typed (deleted automatically after 7 days), the active session per site and the state of the optional support prompt. All of it is kept in chrome.storage.local on the device and is never transmitted.
```

### tabs
```
Used to know which tab is on a tracked site and whether it is the active, focused tab, so only active time is counted, and to send the tab to the extension's own "reclaimed" page when the user chooses Leave. The extension does not read page titles or browsing history beyond the host and path of tracked sites.
```

### alarms
```
Runs the session timers (the "Your 10 minutes are up" screen is triggered when a session expires), the temporary pause of the extension, and the daily clean-up that deletes intentions older than 7 days.
```

### scripting
```
Needed for chrome.scripting.registerContentScripts: when the user adds a site in Options and grants the permission, the extension registers the pause screen for that host (and unregisters it when the site is removed). No code is injected into any site the user did not add; no remote code.
```

### Host permissions (default sites)
```
The built-in sites (youtube.com, tiktok.com, reddit.com, x.com and twitter.com, instagram.com, facebook.com) are declared as host_permissions so the content script can show the pause screen at document_start, before the page is usable, and pause and mute media while it is up. The content script reads only the page address and the visibility/focus state, plus it pauses and mutes media elements. YouTube is path-scoped to the Shorts section in the rules, and the script watches URL changes there because YouTube navigates without reloading.
```

### Optional host permissions (https://*/*)
```
Requested only when the user adds a site of their own in Options (chrome.permissions.request from the click handler), only for that host, and removed again when the user removes the site.
```

### Are you using remote code?
Answer: **No**
```
No. All JavaScript is bundled in the extension package. It does not load or evaluate remote scripts, remote modules or WebAssembly, uses no eval, and its extension-page CSP is script-src 'self'. It makes no network requests of its own.
```

## 8. Data usage disclosures (Privacy practices tab)

Recommended answers. CWS defines "collect" as data transmitted off the user's device or handled by the developer. Reclaim never transmits anything and has no server, so strictly nothing is collected. Recommended checkbox: tick **User activity (time spent on tracked sites and the intentions the user types)**. Leave every other box unticked (the extension never sees payment details; Stripe handles them on its own page).

Everything is stored on the device only and never transmitted, so strictly nothing is "collected", but the honest low-risk disclosure is User activity. Keep Web history unticked: only the host and path of sites the user listed is read, to decide whether to show the pause screen, and no history is stored. If a reviewer asks, the same explanation applies.

Certifications (tick all three):
- I do not sell or transfer user data to third parties, outside of the approved use cases.
- I do not use or transfer user data for purposes that are unrelated to my item's single purpose.
- I do not use or transfer user data to determine creditworthiness or for lending purposes.

## 9. URLs

- Privacy policy URL: https://overcrasher.github.io/reclaim/privacy.html
- Homepage URL: https://overcrasher.github.io/reclaim/
- Support URL: https://github.com/Overcrasher/reclaim/issues

## 10. Screenshots, promo tiles and icon (upload order)

The Chrome Web Store has no per-screenshot caption field. This section documents the upload order and what is on each image in store/images/ (to be created: 1280x800 screenshots).

1. screenshot-1-pause.png: the "What are you here for?" pause screen over a social page (no headline text on the image)
2. screenshot-2-popup.png: "See the time you reclaimed" / the popup with today's time, the 7-day chart and the plant
3. screenshot-3-reclaimed.png: "Nice. A few minutes back." / the reclaimed page with the estimate label
4. screenshot-4-options.png: "Your sites, your rules" / session length, countdown and site list
5. screenshot-5-privacy.png: "Private by design": Everything stays on your device · No ads, no tracking, no accounts · Open source on GitHub

Promo tiles: promo-small-440x280.png and promo-marquee-1400x560.png use the tagline "A calm pause before you scroll" (30 chars).

Store icon: store-icon-128.png (96px artwork in a 128px canvas, from icons/icon128.png).

## 11. Notes for the reviewer

```
Reclaim adds a calm pause before a fixed list of social and video sites. No account or login is needed, and nothing is sent anywhere.

Quick test (about 2 minutes):
1. Load the extension and pin it.
2. Open https://www.reddit.com/ (or tiktok.com, x.com, instagram.com or facebook.com). A full-screen Reclaim pause appears before the page is usable: "What are you here for?", an optional text field and a countdown ring (5 seconds by default). The page underneath cannot be clicked and any playing media is paused.
3. After the countdown, "Go in (10 min)" and "Leave" appear. Click "Go in": the overlay disappears and a 10-minute session starts for that site; other tabs on the same site are not interrupted.
4. Open the toolbar popup: today's time, the 7-day chart, the plant, and "Pause Reclaim for 1 hour".
5. Reload the site and click "Leave" (after the countdown): the tab goes to the extension's own "reclaimed" page ("Nice. ≈ 15 min reclaimed (estimate)"). The number is an estimate and is labelled as one.
6. To see the end-of-session screen quickly: open Options and set the session length to its minimum, or wait for the session to expire.
7. https://www.youtube.com/shorts/ shows the pause only on Shorts pages (the rule is path-scoped; the script watches URL changes because YouTube navigates without reloading).
8. Options > Sites: adding a site triggers Chrome's own permission prompt for that host only (optional_host_permissions); removing it removes the permission.

Optional support: the extension is free. A support banner appears in the popup only at 5, 20, 50 and 100 hours reclaimed, at most once per milestone, 30 days apart, never after "Don't ask again". The same Stripe links are always in Options under "Support this project". Payments happen on Stripe's page (donate.stripe.com or buy.stripe.com); the extension never handles payment data.

Permissions: storage, tabs, alarms, scripting, host permissions for the default sites, and optional https://*/* only for sites the user adds. No remote code, no network requests by the extension. Source: https://github.com/Overcrasher/reclaim
```

## 12. Pre-submission checklist

- [ ] Run `python3 tools/check_release.py --release` and confirm it exits 0 (Stripe links valid and non-test, THANKS_URL matches the manifest, locale limits).
- [ ] Run the unit tests (see README) and load the unpacked folder one last time on real pages.
- [ ] Run `python3 tools/package.py`, which runs the release check and writes dist/reclaim-<version>.zip; upload that zip.
- [ ] Confirm the manifest version is correct (1.0.0 for the first upload; bump for every later upload).
- [ ] Register a Chrome Web Store developer account (one-time US$5 fee) and verify the contact email; set the publisher name to Quantumbyte Labs.
- [ ] Confirm GitHub Pages is live: https://overcrasher.github.io/reclaim/, privacy.html and thanks.html all open.
- [ ] Create the 5 screenshots (1280x800) matching section 10, plus the small promo tile (440x280); the marquee tile (1400x560) is optional.
- [ ] Paste the detailed description in each language (EN, RO, DE, FR, ES; name and short summary come from the package), category, single purpose, permission justifications, data disclosures and reviewer notes.
- [ ] Tick the three certification statements and set remote code to No.
- [ ] After publishing: put the real store URL into docs/index.html (the TODO(store-url) block), the README and the siblings' "More from the same developer" lists.
- [ ] Set visibility (Public) and distribution regions, then submit for review.
