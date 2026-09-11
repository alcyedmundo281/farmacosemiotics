# Depósito en Zenodo: cómo se acuña el DOI

El repositorio **ya está depositado**. La `v0.1.0` se publicó el 11 de
septiembre de 2026 y su DOI de concepto es
[`10.5281/zenodo.22700662`](https://doi.org/10.5281/zenodo.22700662).

Lo que sigue documenta cómo se hizo —porque el orden no se puede invertir y el
error se paga caro— y sirve de procedimiento para cada versión siguiente.

## La trampa, primero

**Zenodo solo acuña un DOI para las releases que ocurren _después_ de activar el
interruptor del repositorio.** No mira hacia atrás. Si se publica la release y
luego se activa la integración, esa release queda sin DOI para siempre: hay que
borrarla, borrar el tag y volver a empezar con otro número de versión.

Por eso el paso 1 no es etiquetar. Es el interruptor.

## El orden

### 1. Activar la integración (una sola vez, en el navegador) — ✅ hecho

1. Entrar en <https://zenodo.org/> con **Log in with GitHub**, de modo que la
   cuenta de Zenodo quede ligada a `alcyedmundo281`.
2. Ir a <https://zenodo.org/account/settings/github/>.
3. Buscar `alcyedmundo281/farmacosemiotics` y poner el interruptor en **ON**.
   Si no aparece, pulsar **Sync now**: Zenodo solo lista lo que GitHub le ha
   dejado ver.

Eso instala un webhook de release en el repositorio. Nada más; no toca el
código.

### 2. Cortar la release

Con el interruptor ya en ON:

```bash
git checkout main && git pull origin main
python scripts/build.py      # no se publica un repositorio con errores
```

Y publicar la release desde <https://github.com/alcyedmundo281/farmacosemiotics/releases/new>,
escribiendo el tag nuevo en `Choose a tag` y dejando que GitHub lo cree al
publicar. **Release**, no solo tag: el webhook escucha `release.published`, y un
tag suelto no lo dispara.

En un par de minutos el registro aparece en
<https://zenodo.org/account/settings/github/> con su DOI.

### 3. Meterlo en la comunidad

`.zenodo.json` declara `communities: powersemiotics`, pero **ese campo hoy no se
aplica solo** en los depósitos que llegan desde GitHub: hay que enviarlo a mano.
Se abre el registro recién creado y se usa **Submit to community** →
`powersemiotics`. Queda pendiente de que la curaduría de la comunidad lo acepte,
que en una comunidad propia es un clic.

Se deja el campo escrito de todos modos: no estorba, documenta la intención y
vuelve a funcionar solo el día que Zenodo lo restablezca.

### 4. Devolver el DOI al repositorio

Zenodo acuña **dos** DOI, y la diferencia importa:

| DOI | qué señala | cuándo se cita |
|---|---|---|
| **de concepto** | el repositorio entero, todas sus versiones | por defecto: resuelve siempre a la última |
| **de versión** | exactamente `v0.1.0` | cuando hay que reproducir un resultado concreto |

Con el DOI de concepto en la mano, se añade a `CITATION.cff`:

```yaml
identifiers:
  - type: doi
    value: 10.5281/zenodo.22700662
    description: DOI de concepto; resuelve siempre a la última versión
```

y la insignia al `README.md`, bajo el título:

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22700662.svg)](https://doi.org/10.5281/zenodo.22700662)
```

`.zenodo.json` no se toca: el DOI lo pone Zenodo, no el repositorio.

## Las versiones siguientes

Ya no hay que volver a tocar el interruptor. Cada release nueva acuña su propio
DOI de versión y lo cuelga del mismo DOI de concepto. Antes de cortarla:

1. subir `version` en `.zenodo.json` y en `CITATION.cff`, y `date-released`;
2. `python scripts/build.py` sin errores;
3. tag y release.

Que ambos ficheros digan la misma versión lo vigila una prueba del contrato, así
que olvidarse de uno de los dos hace fallar CI y no llega a Zenodo.

## Por qué esto no lo hace un script

Zenodo está fuera de la política de egreso de las sesiones de Claude Code en la
web y del CI: `zenodo.org` no se alcanza desde aquí. Automatizarlo exigiría
además un token personal de Zenodo guardado como secreto, y un token capaz de
publicar depósitos a nombre del responsable clínico no es algo que convenga
dejar en manos de un job. Son dos clics una vez, y uno por release.

## Lo que no se hace nunca

- **No se borra un registro publicado.** Un DOI acuñado es una promesa de
  permanencia: si algo sale mal, se publica una versión nueva que lo corrija.
  Zenodo no permite retirar el DOI, y con razón.
- **No se acuña un DOI de un estado que no valida.** `build.py` en verde es
  requisito, no formalidad: lo que se deposita queda citable para siempre.
- **No se inventa el DOI en el README antes de tenerlo.** Es el mismo fallo que
  un `HR` sin PMID, y aquí se llama igual: un identificador con formato
  científico que no resuelve.
