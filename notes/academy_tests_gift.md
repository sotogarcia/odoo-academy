# Academy Tests


# TODO

- [x] Add name to download reports
- [x] Reports could not be saved as attachmets (they are test reports)
- [x] Add security to actions
- [x] Finish to document methods in models
- [x] Add translation file to es_ES


## EXPORT TO MOODLE

### General

- Codificación UTF-8 (no indica si es con BOM o sin el)
- Dos líneas vacías al principio
- Línea ``$CATEGORY: $system$/`` seguida del nombre de la oposición o código Alias
- Otra línea vacía
- Preguntas

### Pregunta

- Título de la pregunta
- Respuestas entre llaves
```
Título de la pregunta. { 
	~ Opción incorrecta 
	= Opción correcta
}
```

### Respuestas

- La opción correcta se marca con = 
- Ñas incorrectas con ~

> Pueden ir en cualquier orden



// texto	Commentario hasta el final de la línea (opcional)