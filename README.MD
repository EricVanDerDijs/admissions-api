## Proyecto dockerizado

Para correrlo utiliza los archivos que se encuentran en la carpeta bin te la siguiente manera:

### Build:

- **Con opciones:**

  `sudo tag="your-bild-tag" ./bin/build`

- **Sin opciones:**

  `sudo ./bin/build`

  **defaults**:
    - tag: admissions-db

### Run:

- **Con opciones:**

  `sudo port="4000" "detach=true" ./bin/run`

- **Sin opciones:**

  `sudo ./bin/run`
  
  **defaults**:
    - port: 3015
    - detach: false
