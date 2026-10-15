# Travel Agent API

Assistente di viaggio intelligente: backend in **FastAPI** con un agente **LangChain / LangGraph** (GPT-4o) che cerca voli e hotel, genera itinerari e fornisce informazioni storico-culturali sulle destinazioni. Il client web e' un'applicazione Laravel (`web_TravelAgent`).

## Architettura

```
travel-agent-api/
├── pyproject.toml / poetry.lock     # dipendenze (Poetry)
├── .env.example                     # template delle variabili d'ambiente
├── tests/
└── travel_agent_api/
    ├── main.py                      # app FastAPI, CORS, registrazione del router
    ├── routes/
    │   └── chat_router.py           # POST /chat/travel-agent
    ├── services/
    │   └── agent_service.py         # classe Agent (agente ReAct di LangGraph)
    └── tools/
        ├── flights_finder.py        # voli  -> SerpApi Google Flights
        ├── hotels_finder.py         # hotel -> SerpApi Google Hotels
        ├── chain_travel_plan.py     # itinerario giorno per giorno (GPT-4o, output strutturato)
        └── chain_historical_expert.py  # contenuti storico-culturali (GPT-4o)
```

Flusso: il client invia la conversazione a `/chat/travel-agent`; `Agent.run` aggiunge il system prompt (con i template markdown di voli, hotel e itinerario) e lascia che l'agente scelga quali tool chiamare; la risposta e' la lista dei messaggi (utente, AI, tool) in JSON.

## Setup

Requisiti: Python >=3.10 e <3.13, Poetry.

```bash
poetry install
cp .env.example .env
```

Compila `.env` con le tue chiavi:

| Variabile | Descrizione |
|---|---|
| `OPENAI_API_KEY` | chiave OpenAI (https://platform.openai.com/settings/organization/api-keys) |
| `SERPAPI_API_KEY` | chiave SerpApi (https://serpapi.com/dashboard) |

`.env` e' nel `.gitignore`: non committarlo mai.

## Avvio

```bash
poetry run uvicorn travel_agent_api.main:app --reload --port 8080
```

Documentazione interattiva e prove: http://127.0.0.1:8080/docs

### Esempio di richiesta

```bash
curl -X POST http://127.0.0.1:8080/chat/travel-agent \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Cerco un hotel 4 stelle nel centro di Roma per due adulti dal 15 al 20 dicembre 2026."}]}'
```

### Esempi di prompt per tool

- **Storia:** "Raccontami la storia dell'antica Roma e la sua influenza sulla civilta' italiana."
- **Hotel:** "Cerco un hotel 4 stelle nel centro di Roma per due adulti dal 15 al 20 dicembre 2026."
- **Voli:** "Cerco voli da FCO a CDG per due adulti, partenza 5 luglio 2027 e ritorno 12 luglio 2027."
- **Itinerario:** "Vorrei un itinerario a Venezia dal 15 al 20 giugno 2027, in coppia, arte e cucina locale, budget 2000 euro, nessuna restrizione alimentare."

Le date vanno nel futuro, altrimenti la ricerca di voli e hotel non restituisce risultati.

## Client web (Laravel)

Il client e' in `../web_TravelAgent` e chiama l'API su `http://127.0.0.1:8080/chat/travel-agent`.

```bash
cd web_TravelAgent
composer install        # richiede l'estensione PHP zip abilitata
npm install
npm run dev
php artisan serve       # http://localhost:8000
```

Il backend deve essere in esecuzione. Il CORS e' configurato per `localhost:8000` e `127.0.0.1:8000`.

## Tracing

Ogni tool e l'endpoint stampano un separatore con il proprio nome nel terminale del server, cosi' si vede cosa viene eseguito e in che ordine. In piu' `Agent.run` stampa il numero di messaggi ricevuti, i **tool usati dall'agente** e il **tempo di esecuzione** (vedi sotto).

## Modifiche rispetto alle guide

Il codice segue le guide del corso, con questi cambiamenti:

- **Python:** `requires-python` impostato a `>=3.10,<3.13` (la versione delle guide, `>=3.9`, e' incompatibile con le dipendenze attuali, ad esempio `python-dotenv`). Struttura piatta `travel_agent_api/` senza `src/`.
- **Import:** `langchain_core.prompts` al posto di `langchain.prompts` (il pacchetto `langchain` non e' installato).
- **`chain_historical_expert`:** restituisce `result.content` (stringa) invece dell'oggetto messaggio.
- **`chain_travel_plan`:** il prompt include le istruzioni di formato del parser (`get_format_instructions`) e il testo e' passato come variabile del template, per evitare errori con le graffe del JSON.
- **`hotels_finder`:** se la risposta non contiene `properties` restituisce la risposta intera (con il messaggio di errore) invece di un `KeyError`.
- **`flights_finder`:** la variabile con i parametri della richiesta e' stata rinominata `search_params` (nelle guide veniva sovrascritta); `stops` impostato a `2` (voli diretti o con un solo scalo).
- **`chat_router`:** gli errori dell'agente vengono restituiti come `HTTPException` 500 con il dettaglio, come descritto nel docstring.
- **`agent_service`:** corretto il refuso `convesation_history`; aggiunti i giorni di esempio mancanti nel template dell'itinerario.

## Personalizzazione: tracing dell'agente

In `services/agent_service.py`, il metodo `Agent.run` ora stampa nel terminale:

1. quanti messaggi ha ricevuto;
2. quali **tool l'agente ha deciso di chiamare** (leggendo i `tool_calls` dei messaggi di risposta);
3. quanto tempo e' durata l'esecuzione.

Esempio di output:

```
********************************************************************************
Agent.run - messaggi ricevuti: 1
********************************************************************************
...
Agent.run - tool usati: ['hotels_finder']
Agent.run - tempo di esecuzione: 12.3s
```

Serve a capire come ragiona l'agente (quali tool sceglie per ogni richiesta) e dove va il tempo di risposta.
