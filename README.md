# ChatServer WebSocket in Python

Server di chat asincrono sviluppato in Python con `asyncio` e `websockets`.   Gestisce più client in tempo reale con autenticazione, broadcasting dei messaggi e gestione automatica delle disconnessioni e riconnessioni.  

---

## 🚀 Funzionalità principali

- 🔐 Autenticazione utenti da file `users.txt`
- 🔄 Gestione connessioni e disconnessioni in tempo reale
- 🧩 Utilizzo di `asyncio.Lock()` per evitare race condition
- 🧠 Logging avanzato con `rich` sia su terminale che su file
- 📁 Struttura modulare e facilmente estendibile

---

## 📂 Struttura del progetto

```
progetto_server/
│
├── server.py              # Entrypoint e logica principale
├── utils.py               # Funzioni trasversali
├── users.txt              # File contenente utenti autorizzati
├── requirements.txt       # Librerie richieste
```

---

## 🧩 Come eseguire

### 1. Clona la repository
```bash
git clone https://github.com/misterCipo/progetto_server.git
cd progetto_server
```

---

### 2. Crea e attiva l'ambiente virtuale

#### 🪟 Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### 🐧 macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Installa le librerie necessarie
#### Windows
```bash
pip install -r requirements.txt
```

#### macOS / Linux
```bash
pip3 install -r requirements.txt
```

---

### 4. Avvia il server
Puoi usare i parametri opzionali `-H` (host) e `-p` (porta), oppure lasciare i valori di default.

#### Esempio
```bash
python server.py -H "localhost" -p 3199
```
(Oppure `python3` su macOS/Linux)

---

## 🧱 Librerie utilizzate

- **Python 3.10+**
- **asyncio** per la gestione asincrona delle connessioni
- **rich** per il logging colorato e strutturato
- **argparse** per la gestione dei parametri CLI

---

## 🧾 Licenza

Questo progetto è distribuito sotto licenza **MIT**. Puoi usarlo, modificarlo e distribuirlo liberamente, a patto di mantenere i crediti originali.

---

## 👤 Autore

**Marco Cerbella e Daniele Minelli **  
Progetto didattico per lo studio di server asincroni e gestione concorrente in Python.
