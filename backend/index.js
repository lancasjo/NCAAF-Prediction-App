const express = require('express');
const MongoClient = require('mongodb').MongoClient;
const cors = require('cors');
const app = express();
const port = 3000; // Choose a port number

const uri = "mongodb+srv://jrlancaste:bugbugbug@sportsbetting.vqijjoh.mongodb.net/?retryWrites=true&w=majority";

const corsOptions = {
  origin: '*',
  methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
  credentials: true,
  optionsSuccessStatus: 204,
};

app.use(cors(corsOptions));

const client = new MongoClient(uri);

app.get('/api/data', async (req, res) => {
    try {
      
      await client.connect();
  
      const database = client.db('game-database'); // Replace with your database name
      const collection = database.collection('weeks-collection'); // Replace with your collection name
  
      const data = await collection.find({}).toArray();
      res.json(data);
    } catch (error) {
      console.error('Error fetching data:', error);
      res.status(500).send('Internal Server Error');
    } finally {
      client.close();
    }
  });
  
app.get('/api/data/teams', async (req, res) => {
  try {
      await client.connect();
      const database = client.db('game-database'); // Replace with your database name
      const collection = database.collection('weeks-collection'); // Replace with your collection name

      const team_name = req.query.team;
  
      const data = await collection.find({"Team" : team_name }).toArray();
      res.json(data);
  } catch (error) {
      console.error('Error fetching data:', error);
      res.status(500).send('Internal Server Error');
  } finally {
      client.close();
  }});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
  });
