# Protector GLog 4G

Protector imprimible en 3D para el registrador SigmaWit GLog 4G (GLogm3 / GLogs1), versión invernadero.
Piezas: placa, techo, persiana de lamas horizontales y cuna a medida que sujeta el equipo sin tornillos.
Impresión: Creality K1, PETG, sin soportes.

## Carpetas
- `Persiana_GLog/` — **entrega actual**: STL listos para imprimir (`STL/`), imágenes y `LEEME_impresion_3D.txt` (perfil, montaje, historial de versiones y verificación).
- `Protector_GLog/` — protector original (placa, techo, repisa, plano PDF).
- `render_blender/` — scripts de Blender 5.2 que generan las piezas (`persiana_vN.py`, `cuna_vN.py`), la verificación del ensamble (`verificar.py`) y los renders (`escena.py`).
- `Imagenes_para_cliente/` — renders para presentar.

## Regenerar
```
blender -b -P render_blender/persiana_v5.py
blender -b -P render_blender/cuna_v1.py
blender -b -P render_blender/verificar.py -- persiana_v5 cuna_v1
```
Las piezas se versionan (`_v1`, `_v2`…) y nunca se sobrescriben las anteriores.

## Pendiente
- Medir el equipo real y ajustar `EQ_W, EQ_H, EQ_T` en `cuna_v1.py`.
- Imprimir `5_cuna_v1_prueba_ajuste.stl` y probar el ajuste.
- Prueba de agua con el conjunto armado.
