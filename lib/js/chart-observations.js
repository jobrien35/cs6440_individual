  
  //  allow adding sodium and potassium entries
  document.getElementById('add_sodium').addEventListener('click', addSodiumEntry);
  document.getElementById('add_potassium').addEventListener('click', addPotassiumEntry);


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
  var value = parseInt(document.getElementById('sodium_input').value)/1000; // match fhir units of grams
  var entry = {
    "date" : new Date().toISOString(),  // When the entry was made (YYYY-MM-DDTHH:mm:ss.SSSSZ)
    "value" : value
  }
  console.log('new sodium point:');
  console.log(entry);
  // TODO: check for arbitrary duration between entries? 
  extendData('sodium_div', entry.value, entry.date);
  var series = document.getElementById('sodium_div').data;
  console.log("added entry of: "+ value + " on: " + new Date(series[0].x[series[0].x.length - 1]));
  console.log(' sodium, potassium, bp existing datasets:')
  console.log(document.getElementById('sodium_div').data);
  console.log(document.getElementById('potassium_div').data);
  console.log(document.getElementById('bp_div').data);

}

function addPotassiumEntry() {
  var value = parseInt(document.getElementById('potassium_input').value)/1000; // match fhir units
  var entry = {
    "date" : new Date().toISOString(),  // When the entry was made (YYYY-MM-DDTHH:mm:ss.SSSSZ)
    "value" : value
  }
  extendData('potassium_div', entry.value, entry.date);
  console.log('new potassium point:');
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
  x: simulated_dates,
  y: [2, 2.5, 1.2],
  mode: 'lines+markers',
  connectgaps: true,
  name: 'Sodium',
};

var simulated_potassium = {
  x: simulated_dates,
  y: [3, 2, 0.5],
  mode: 'lines+markers',
  connectgaps: true,
  name: 'Potassium',
};

var simulated_systolic = {
  x: simulated_bp_dates,
  y: [120, 145, 160],
  mode: 'lines+markers',
  connectgaps: true,
  name: 'Systolic',
};

var simulated_diastolic = {
  x: simulated_bp_dates,
  y: [80, 85, 90],
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

console.log('b: ' + b); // b is in get-data
var count = 0;
var d = null;
var c = fetch('./lib/fhir/Lindsey52_Ledner144_5791f6fc-11ab-e632-5fd7-3135662b1b44.json', {mode: 'cors'})
.then(data=>{return data.json()})
  .then(res=>{
    d = res;
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

var w = null;
var q = fetch('https://jobrien35-cs6440.herokuapp.com/', {mode: 'cors'})
.then(data=>{return data.json()})
  .then(res=>{
    w = res;
    console.log("w: ")
    console.log(w);
    return res;
  }).catch(err => { // then res
  console.log(err);
});