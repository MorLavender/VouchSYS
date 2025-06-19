const express = require('express');
const swaggerUi = require('swagger-ui-express');
const fs = require('fs');
const app = express();

const swaggerDocument = JSON.parse(fs.readFileSync('./openapi/VouchSys_OpenAPI_Spec.json', 'utf8'));

app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

app.listen(3000, () => console.log('Server running at http://localhost:3000'));
