const express = require('express');
const cors = require('cors'); 
const app = express();  

app.use(cors({ 
    origin: 'http://127.0.0.1:8080/' 
}));


// Define a list of opportunities (dummy data)
const opportunities = [
  {
    opp_id: 1,
    opp_type: "internship",
    opp_title: "Software Engineering Intern",
    address_line_1: "123 Main St",
    address_line_2: "Suite 100",
    address_line_3: "San Francisco, CA 94105",
    company_id: 1
  },
  { 
    opp_id: 2,
    opp_type: "placement",
    opp_title: "Software Engineer",
    address_line_1: "456 First St",
    address_line_2: "Floor 5",
    address_line_3: "Mountain View, CA 94043",
    company_id: 2
  },
  {
    opp_id: 3,
    opp_type: "placement",
    opp_title: "Product Manager",
    address_line_1: "789 Second St",
    address_line_2: "Suite 200",
    address_line_3: "Palo Alto, CA 94303",
    company_id: 3
  }
];  

// Define a route handler for GET requests on "/api/poc/opportunities"
app.get('/api/poc/opportunities', (req, res) => {
  res.send(opportunities);
});  

app.listen(5500, () => {
  console.log('Server listening on port 5500');
});

