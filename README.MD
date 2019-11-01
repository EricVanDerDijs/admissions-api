## Proyecto dockerizado

Para correrlo utiliza los archivos que se encuentran en la carpeta bin te la siguiente manera:

### Build:

Ejecuta el proceso de *build* de docker para el proyecto

- **Con opciones:**

  `sudo tag="your-bild-tag" ./bin/build`

- **Sin opciones:**

  `sudo ./bin/build`

  **defaults**:
    - tag: admissions-db

### Run:

Corre el proyecto en un contenedor docker

- **Con opciones:**

  `sudo port="4000" detach="true" init_db="True" tag="2" ./bin/run`

- **Sin opciones:**

  `sudo ./bin/run`
  
  **defaults**:
    - port: 3010
    - detach: false
    - tag: "" (etiqueta de la base de datos, requerido para crear un nuevo volumen para el contenedor)
    - init_db: False

### Withreplicas:

Corre 3 el proyecto en 3 contenedores docker en background (detached), cada uno con una base de datos independiente

- **Con opciones:**

  `sudo init_db="True" ./bin/withreplicas`

- **Sin opciones:**

  `sudo ./bin/withreplicas`
  
  **defaults**:
    - init_db: False
