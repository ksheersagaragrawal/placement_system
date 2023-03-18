const express = require('express');
const path = require('path');

const app = express();

app.get('/student', (req, res) => {
    res.sendFile(path.join(__dirname, './frontend/student_pages/student_dashboard.html'));
});

app.get('/student/profile', (req, res) => {
    res.sendFile(path.join(__dirname, './frontend/student_pages/student_profile.html'));
}); 

app.get('/student/resume', (req, res) => {
    res.sendFile(path.join(__dirname, './frontend/student_pages/resume_page.html'));
});  

app.get('/student/opportunities', (req, res) => {
    res.sendFile(path.join(__dirname, './frontend/student_pages/opportunity_list.html'));
});   

app.get('/poc', (req, res) => {
    res.sendFile(path.join(__dirname, './frontend/poc_pages/hr_dashboard.html'));
});  

app.get('/poc/my-opportunities', (req, res) => {
    res.sendFile(path.join(__dirname, './frontend/poc_pages/opportunity_page.html'));
});  

app.get('/cds/student', (req, res) => {
    res.sendFile(path.join(__dirname, './frontend/cds_pages/cds_student_profiles.html'));
})

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

