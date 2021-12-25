const express = require('express')
const bodyParser = require('body-parser');
const { spawn } = require('child_process');
const crypto = require('crypto');

const app = express()

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json())

app.get('/', (req, res)=>{
    res.sendFile(__dirname + "/index.html")
})

app.post('/evaluate', (req, res)=>{
    let username = req.body.username
    let password = req.body.password

    const process = spawn("python3", ["AutoEvaluate.py", username, password], {
       cwd: __dirname
    });

    output = ""

    process.stdout.on('data', (data) => {
        output += data
    });
      
    process.stderr.on('data', (data) => {
        output += data
    });

    process.on('close', (code)=>{
        res.json({
            "err": code,
            "output": output
        })
        console.log(output)
    })
})


console.log("listening on 80...")
app.listen(80);