# Adeguamento ISTAT del canone e scadenze del contratto

Utility di Giuliato&Battistin (giuliatobattistin.it): calcola l'aggiornamento annuale del canone di locazione con l'indice ISTAT FOI, prepara la lettera per l'inquilino (italiano e inglese) e costruisce lo scadenzario del contratto con un file `.ics` per il calendario.

Tutto avviene nel browser: nessun dato viene inviato o salvato.

## Quota applicata

La quota proposta dipende dal tipo di contratto. Se la clausola indica una percentuale, si usa quella entro il limite del tipo.

| Situazione | Quota proposta | Condizione |
| --- | --- | --- |
| Commerciale ordinario 6+6 | 75% | Aggiornamento previsto dal contratto; se la clausola indica meno, si usa quella. |
| Non abitativo con durata iniziale superiore al minimo (es. 7+6) | Quella della clausola, eventualmente 100% | Il 100% non è automatico. |
| Abitativo a canone libero 4+4, senza cedolare | 100% (da confermare) | Serve la clausola; se indica il 75%, si applica il 75%. |
| Abitativo a canone concordato, senza cedolare | Fino al 75% | Verificare accordo territoriale e clausola. |
| Cedolare secca attiva | Aggiornamento disabilitato | Sospeso per il periodo dell'opzione. |
| Nessuna clausola di aggiornamento | Nessun aggiornamento | La percentuale scelta nel calcolatore non rende dovuto l'aumento. |

## Dati ISTAT e aggiornamento automatico

- `data/foi.json` contiene la variazione annua dell'indice FOI (senza tabacchi) dal 2020, letta dall'API SDMX ufficiale ISTAT.
- Il blocco `FOI_DATA` dentro le due pagine è una copia degli stessi dati: la pagina non fa richieste esterne.
- La GitHub Action `.github/workflows/update-foi.yml` gira ogni giorno dal 14 al 28 del mese (ISTAT diffonde i dati a metà mese), esegue `scripts/update_foi.py` e fa commit solo se ci sono dati nuovi. Si può lanciare a mano da Actions > "Aggiorna indici FOI ISTAT" > Run workflow.
- Se l'API non risponde o i dati non passano i controlli (mesi consecutivi, valori plausibili) lo script esce con errore e non modifica nulla: GitHub segnala l'esecuzione fallita.
- Se ISTAT cambia base o codici delle serie, vanno aggiornati gli identificativi in `scripts/update_foi.py`.

## Versioni e inserimento nel sito

La pagina esiste in italiano (`Adeguamento_ISTAT_canone.html`) e in inglese (`Adeguamento_ISTAT_canone_en.html`). L'aggiornamento mensile dei dati riscrive entrambe. Per la versione inglese si usa lo stesso codice con questo `src`:

`https://raw.githack.com/Mgiuly/Adeguamento_ISTAT_canone/refs/heads/main/Adeguamento_ISTAT_canone_en.html`

Versione italiana:

```html
<iframe
  src="https://raw.githack.com/Mgiuly/Adeguamento_ISTAT_canone/refs/heads/main/Adeguamento_ISTAT_canone.html"
  style="width: 100%; height: 1500px; border: none; display: block;"
  scrolling="no">
</iframe>

<script>
window.addEventListener('message', function (e) {
  var d = e.data;
  if (!d || d.source !== 'gb-calcolatore' || d.type !== 'height') return;
  var frames = document.querySelectorAll('iframe');
  for (var i = 0; i < frames.length; i++) {
    if (frames[i].contentWindow === e.source) {
      frames[i].style.height = d.height + 'px';
    }
  }
});
</script>
```
