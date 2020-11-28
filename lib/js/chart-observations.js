  
//  allow adding sodium and potassium entries
document.getElementById('add_sodium').addEventListener('click', addSodiumEntry);
document.getElementById('add_potassium').addEventListener('click', addPotassiumEntry);
document.getElementById('add_bp').addEventListener('click', addBPEntry);
document.getElementById('post_mfp').addEventListener('click', postMFP);
document.getElementById('fhir_file').addEventListener('change', uploadFhir);

var tempPid = retrievePid();
document.getElementById('patient_id').innerHTML = tempPid;
if (tempPid !== '...') {
  console.log('initial temp: ' + tempPid)
  parsePatientObservations(tempPid)
}
function extendData(div_name, value, date) {
  Plotly.extendTraces(div_name, { // div name
    y: [[value]], // y val
    x: [[date]], // x val
  }, [0]) // list of series to append to
}

function extendBPData(div_name, systolic_value, diastolic_value, date) {
  Plotly.extendTraces(div_name, { // div name
    y: [[systolic_value], [diastolic_value]], // y values
    x: [[date], [date]], // x values, dates are same for both readings
  }, [0, 1]) // match order from initial data, systolic is 0, diastolic is 1-index
}


function addSodiumEntry() {
  var value = parseInt(document.getElementById('sodium_input').value)/1000; // match loinc units of grams
  var entry = {
    "date" : new Date().toISOString(),  // When the entry was made (YYYY-MM-DDTHH:mm:ss.SSSSZ)
    "value" : value
  }
  console.log('new sodium point:');
  console.log(entry);
  // TODO: check for 24hr duration between entries? 
  extendData('sodium_div', entry.value, entry.date);
  var series = document.getElementById('sodium_div').data;
  console.log("added entry of: "+ value + " on: " + new Date(series[0].x[series[0].x.length - 1]));
  console.log(' sodium, potassium, bp existing datasets:')
  console.log(document.getElementById('sodium_div').data);
  console.log(document.getElementById('potassium_div').data);
  console.log(document.getElementById('bp_div').data);

}


function addPotassiumEntry() {

  var value = parseInt(document.getElementById('potassium_input').value)/1000; // match loinc units of grams
  if (Number.isNaN(value)) {
    console.log('potassium invalid');
    return
  }
  var entry = {
    "date" : new Date().toISOString(),  // When the entry was made (YYYY-MM-DDTHH:mm:ss.SSSSZ)
    "value" : value
  }
  extendData('potassium_div', entry.value, entry.date);
  console.log('new potassium point:');
  console.log(entry);
}


function addBPEntry() {
  var systolic_value = parseInt(document.getElementById('systolic_input').value);
  var diastolic_value = parseInt(document.getElementById('diastolic_input').value);
  var entry = {
    "date" : new Date().toISOString(),  // When the entry was made (YYYY-MM-DDTHH:mm:ss.SSSSZ)
    "systolic_value" : systolic_value,
    "diastolic_value" : diastolic_value
  }
  extendBPData('bp_div', systolic_value, diastolic_value, entry.date);
  console.log('new bp point:');
  console.log(entry);
}


//helper function to get quanity from an observation resoruce.
function getQuantityValueOnly(ob) {
  if (typeof ob != 'undefined' &&
    typeof ob.valueQuantity != 'undefined' &&
    typeof ob.valueQuantity.value != 'undefined' &&
    typeof ob.valueQuantity.unit != 'undefined') {
    return Number(parseFloat((ob.valueQuantity.value)).toFixed(2));
  } else {
    return undefined;
  }
}

// helper function to get both systolic and diastolic bp
function getBloodPressureValueOnly(BPObservations, typeOfPressure) {
  var formattedBPObservations = [];
  BPObservations.forEach(function(observation) {
    var BP = observation.component.find(function(component) {
      return component.code.coding.find(function(coding) {
        return coding.code == typeOfPressure;
      });
    });
    if (BP) {
      observation.valueQuantity = BP.valueQuantity;
      formattedBPObservations.push(observation);
    }
  });
  return getQuantityValueOnly(formattedBPObservations[0]);
}

var simulated_dates = ['2020-03-03 22:23:00', '2020-03-04 22:23:00', '2020-03-05 22:23:00']
var simulated_bp_dates = ['2016-07-01 22:23:00', '2016-07-02 22:23:00', '2016-07-03 22:23:00']

var simulated_sodium = {
//  x: simulated_dates,
//  y: [2, 2.5, 1.2],
  x: [],
  y: [],
  mode: 'lines+markers',
  connectgaps: true,
  name: 'Sodium',
};

var simulated_potassium = {
//  x: simulated_dates,
//  y: [3, 2, 0.5],
  x: [],
  y: [],
  mode: 'lines+markers',
  connectgaps: true,
  name: 'Potassium',
};

var simulated_systolic = {
//  x: simulated_bp_dates,
//  y: [120, 145, 160],
  x: [],
  y: [],
  mode: 'lines+markers',
  connectgaps: true,
  name: 'Systolic',
};

var simulated_diastolic = {
//  x: simulated_bp_dates,
//  y: [80, 85, 90],
  x: [],
  y: [],
  mode: 'lines+markers',
  connectgaps: true,
  name: 'Diastolic',
};

var layout = {
  yaxis: {
    title: 'ingested (g)',
    titlefont: { size:12 },
  },
  xaxis: {
    title: 'Date',
    titlefont: { size:12 },
    automargin: true,
  },
  showlegend: false,
  autosize: false,
  width: 500,
  height: 300,
  margin: {
    l: 50,
    r: 20,
    b: 20,
    t: 50,
    pad: 4
  },
};

var bp_layout = {
  yaxis: {
    title: "measured mm[Hg]",
    titlefont: { size:12 },
  },
  xaxis: {
    title: 'Date',
    titlefont: { size:12 },
    automargin: true,
  },
  showlegend: false,
  autosize: false,
  width: 500,
  height: 300,
  margin: {
    l: 50,
    r: 20,
    b: 20,
    t: 50,
    pad: 4
  },
};

var sodium_plot = Plotly.newPlot('sodium_div', [simulated_sodium], layout);
var potassium_plot = Plotly.newPlot('potassium_div', [simulated_potassium], layout);
var bp_plot = Plotly.newPlot('bp_div', [simulated_systolic, simulated_diastolic], bp_layout);


function parsePatientObservations(apid) {
  var count = 0;
  var d = null;
  var q1 = 'https://r4.smarthealthit.org/Observation?patient='
  var q2 = q1.concat(apid)
  var c = fetch(q2, {mode: 'cors'})
  .then(data=>{
    return data.json()
  })
    .then(res=>{
      d = res;
      console.log('d')
      console.log(d)
      d.entry.map((idx)=> {
        var curr_item = idx.resource; // The actual object you would normally get from fhir if this was POSTd successfully

        FHIR.oauth2.ready().then(function(client) {
          var observations = client.byCodes(curr_item, 'code');
          var systolicbp = getBloodPressureValueOnly(observations('85354-9'), '8480-6');
          var diastolicbp = getBloodPressureValueOnly(observations('85354-9'), '8462-4');
          var obs_date = new Date(curr_item.effectiveDateTime);
          if (curr_item.resourceType == "Observation" && curr_item.code.text == "Blood Pressure") {
            if (obs_date > new Date(2020)) { // filter out old readings
              // console.log("count: " + count + " bp-> dia: " + diastolicbp + " sys: " + systolicbp + " date: " + obs_date);
              extendBPData('bp_div', systolicbp, diastolicbp, obs_date);
            }
          }

          if (curr_item.resourceType == 'Observation' && curr_item.code.text == "Sodium intake 24 hour Estimated") {
            // console.log("count: " + count + " sodium entry: " + getQuantityValueOnly(curr_item) + " date: " + obs_date);
            extendData('sodium_div', getQuantityValueOnly(curr_item), obs_date)
          }

          if (curr_item.resourceType == 'Observation' && curr_item.code.text == "Potassium intake 24 hour Estimated") {
            // console.log("count: " + count + " potassium entry: " + getQuantityValueOnly(curr_item) + " date: " + obs_date);
            extendData('potassium_div', getQuantityValueOnly(curr_item), obs_date)
          }
          count = count + 1;

        }) // fhir oauth
      }) // map
      return res;
    }).catch(err => { // then res
    console.log(err);
  });
} // parsePatientObservations

var w = null;
var q = fetch('https://jobrien35-cs6440.herokuapp.com/')
.then(data=> { return data.json() })
  .then(res=> {
    w = res;
    console.log("heroku root: ")
    console.log(w);
    return res;
  }).catch(err => { // then res
  console.log(err);
});


// Example POST method implementation:
// https://developers.google.com/web/updates/2015/03/introduction-to-fetch#fetch
async function uploadFhir() {
  // Default options are marked with *
  var file = document.getElementById('fhir_file').files[0];
  var pid = document.getElementById('patient_id').innerHTML;
  var formData = new FormData();
  formData.append("fd", file);
  formData.append("pid", pid);

  fetch('https://jobrien35-cs6440.herokuapp.com/api/v1/nutrition/upload', {
    method: 'POST', mode: 'cors', body: formData})
    .then(
      function(response) {
        console.log(response.status)
        // Examine the text in the response
        response.json().then(function(data) {
          console.log('uploaded response:')
          console.log(data);
          pid = data.pid
          document.getElementById('patient_id').innerHTML = pid
          storePid(pid);
          console.log(pid)
          parsePatientObservations(pid);
        });
      }
    )
    .catch(function(err) {
      console.log('Fetch Error :-S', err);
    });
}


async function postMFP() {

  var u = document.getElementById("u").value;
  var p = document.getElementById("p").value;
  var start = document.getElementById("start").value;
  var end = document.getElementById("end").value;
  var pid = document.getElementById("patient_id").innerHTML;
  var formData = new FormData();
  formData.append("u", u);
  formData.append("p", p);
  formData.append("start", start);
  formData.append("end", end);
  if (pid !== "...") {
    formData.append("pid", pid);
    console.log("pid not ...");
  }
  fetch("https://jobrien35-cs6440.herokuapp.com/api/v1/nutrition/mfp", {
    method: "POST", mode: "cors", body: formData})
    .then(
      function(response) {
        console.log(response.status)
        console.log(response)
        // Examine the text in the response
        response.json().then(function(data) {
          console.log(data);
          document.getElementById("patient_id").innerHTML = data.pid
        });
      }
    )
    .catch(function(err) {
      console.log("Fetch Error :-S", err);
    });
}