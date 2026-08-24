# costos/

**Aquí y solo aquí van los precios.** Un `precio` dentro de `farmacos/` o
`fichas/` es un error que `build.py` rechaza.

## Por qué están fuera del núcleo

No existe una fuente de precios internacional que sea a la vez libre,
comparable entre países y actual. Las que hay —la *International Medical
Products Price Guide* de MSH, las encuestas de precios de la OMS y HAI, los
mecanismos de compra conjunta— cubren distintos fármacos, distintos años y
distintos eslabones de la cadena.

Meter un precio en la ficha internacional tendría dos consecuencias, ambas
malas: la volvería falsa en cuanto cruza una frontera, y la haría envejecer
sin que se note. Un dato clínico de 1998 sigue siendo cierto; un precio de
1998 es basura con aspecto de dato.

Por eso el precio es un **overlay**: se superpone a la ficha cuando alguien lo
pide para un país concreto, y nunca forma parte del registro que se cita.

## Un fichero por país

`costos/<iso-3166-alpha-2>.yaml`, en minúsculas: `ec.yaml`, `co.yaml`,
`es.yaml`.

```yaml
pais: EC
moneda: USD
fuente:
  nombre: Nombre del listado oficial de precios
  organismo: Quién lo publica
  url: https://…
  fecha_publicacion: '2026-01-15'
consultado: '2026-08-24'

precios:
  - farmaco: 'FS:0001'
    presentacion: 'comprimido 500 mg'
    precio_unitario: 0.04
    envase: 30
    nota: precio techo de venta al público
```

## Reglas

- **Fuente, moneda y fecha, siempre.** Un precio sin las tres no es un precio,
  es un rumor con decimales. `consultado` es obligatorio.
- **Se referencia al fármaco por su código `FS:`**, no por el nombre: los
  nombres comerciales cambian de país en país y de año en año.
- **No se convierte a otra moneda.** Convertir exige una fecha de tipo de
  cambio que nadie va a mantener, y produce una cifra que no aparece en
  ninguna fuente.
- **No se compara entre países dentro del fichero.** Si algún día hace falta
  una comparación, la calcula un script a partir de estos ficheros, con sus
  supuestos escritos.

Ecuador es el primer overlay previsto —es de donde viene el material original
de este proyecto—, pero no tiene ningún estatus especial: es un país más.
