const express = require('express');
const path = require('path');

const app = express();

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'student_dashboard.html'));
});

app.get('/profile', (req, res) => {
    res.sendFile(path.join(__dirname, 'student_profile.html'));
}); 

app.get('/resume', (req, res) => {
    res.sendFile(path.join(__dirname, 'resume_page.html'));
});  

app.get('/opportunities', (req, res) => {
    res.sendFile(path.join(__dirname, 'opportunity_list.html'));
});  

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

