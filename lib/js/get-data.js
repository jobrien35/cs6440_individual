//adapted from the cerner smart on fhir guide. updated to utalize client.js v2 library and FHIR R4

// helper function to process fhir resource to get the patient name.
function getPatientName(pt) {
  if (pt.name) {
    var names = pt.name.map(function(name) {
      return name.given.join(" ") + " " + name.family;
    });
    return names.join(" / ")
  } else {
    return "anonymous";
  }
}

// display the patient name gender and dob in the index page
function displayPatient(pt) {
  document.getElementById('patient_name').innerHTML = getPatientName(pt);
  document.getElementById('gender').innerHTML = pt.gender;
  document.getElementById('dob').innerHTML = pt.birthDate;
}

//function to display list of medications
function displayMedication(meds) {
  // console.log(meds);
  meds.forEach(function(med) {
    // console.log(med);
    med_list.innerHTML += "<li> " + med + "</li>";
  })
}

//helper function to get quanity and unit from an observation resoruce.
function getQuantityValueAndUnit(ob) {
  if (typeof ob != 'undefined' &&
    typeof ob.valueQuantity != 'undefined' &&
    typeof ob.valueQuantity.value != 'undefined' &&
    typeof ob.valueQuantity.unit != 'undefined') {
    return Number(parseFloat((ob.valueQuantity.value)).toFixed(2)) + ' ' + ob.valueQuantity.unit;
  } else {
    return undefined;
  }
}

// helper function to get both systolic and diastolic bp
function getBloodPressureValue(BPObservations, typeOfPressure) {
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
  return getQuantityValueAndUnit(formattedBPObservations[0]);
}

// create a patient object to initalize the patient
function defaultPatient() {
  return {
    height: {
      value: ''
    },
    weight: {
      value: ''
    },
    sys: {
      value: ''
    },
    dia: {
      value: ''
    },
    ldl: {
      value: ''
    },
    hdl: {
      value: ''
    },
    note: 'No Annotation',
  };
}

// helper function to display the annotation on the index page
function displayAnnotation(annotation) {
  note.innerHTML = annotation;
}

//function to display the observation values you will need to update this
function displayObservation(obs) {
  hdl.innerHTML = obs.hdl;
  ldl.innerHTML = obs.ldl;
  sys.innerHTML = obs.sys;
  dia.innerHTML = obs.dia;
  weight.innerHTML = obs.weight;
  height.innerHTML = obs.height;
  //note.innerHTML = obs.ano;
}

//once fhir client is authorized then the following functions can be executed
FHIR.oauth2.ready().then(function(client) {

  // get patient object and then display its demographics info in the banner
  client.request(`Patient/${client.patient.id}`).then(
    function(patient) {
      displayPatient(patient);
      console.log('patient')
      console.log(patient);
    }
  );

  // get observation resoruce values
  // you will need to update the below to retrive the weight and height values
  // get observation resoruce values
  var query = new URLSearchParams();

  query.set("patient", client.patient.id);
  query.set("_count", 100);
  query.set("_sort", "-date");  // Try this to fetch fewer pages
  query.set("code", [           // LongName
    'http://loinc.org|29463-7', // Body weight
    'http://loinc.org|8302-2',  // Body height
    'http://loinc.org|8462-4',  // Diastolic blood pressure
    'http://loinc.org|8480-6',  // Systolic blood pressure
    'http://loinc.org|2085-9',  // Cholesterol in HDL [Mass/volume] in Serum or Plasma
    'http://loinc.org|2089-1',  // Cholesterol in LDL [Mass/volume] in Serum or Plasma
    'http://loinc.org|18262-6', // Cholesterol in LDL [Mass/volume] in Serum or Plasma by Direct assay
    'http://loinc.org|55284-4', // (SMART) Blood pressure systolic and diastolic (synthea generated : 85354-9)
    'http://loinc.org|3141-9',  // Body weight Measured
  ].join(","));

  var weightID = ""; // observation ID for weight so we can add annotation to it at any time from the gui.
  var weightObs = null;
  client.request("Observation?" + query, {
    pageLimit: 0, // get all pages
    flat: true // return flat array of Observation resources
  }).then(
    function(ob) {
      console.log("observation")
      console.log(ob);

      // group by all codes into a map
      var byCodes = client.byCodes(ob, 'code');
      // get all observations with given code into flag array
      var height = byCodes('8302-2');
      var weight = byCodes('29463-7');
      var systolicbp = getBloodPressureValue(byCodes('55284-4'), '8480-6');
      var diastolicbp = getBloodPressureValue(byCodes('55284-4'), '8462-4');
      var hdl = byCodes('2085-9');
      var ldl = byCodes('2089-1');
      var ldl2 = byCodes('18262-6');

      var p = defaultPatient();

      var ldlValue = getQuantityValueAndUnit(ldl[0]);
      var ldlValue2 = getQuantityValueAndUnit(ldl2[0]);
      console.log(" 2089-1: " + ldlValue);
      console.log("18262-6: " + ldlValue2);
      // account for very common LDL value in SMART patient records
      if (typeof ldlValue == 'undefined' && typeof ldlValue2 != 'undefined') {
        ldlValue = ldlValue2;
      }
      p.ldl = ldlValue;
      p.hdl = getQuantityValueAndUnit(hdl[0]);

      if (typeof weight[0] != 'undefined' && typeof weight[0].note != 'undefined') {
        // oldest is last, so use first note to display the latest
        // var oldest = ano.length - 1;
        p.ano = weight[0].note[0].text;
        console.log("ano: " + p.ano);

      } else {
        p.ano = p.note;
        console.log("note: " + p.note);
      }
      // need to persist to proper weight observation id
      console.log("weight[0]");
      console.log(weight[0]);
      if (typeof weight[0] != 'undefined' && typeof weight[0].id != 'undefined') {
        weightID = weight[0].id;
      }
      weightObs = weight[0];
      console.log("weight id: " + weightID);

      p.height = getQuantityValueAndUnit(height[0]);
      p.weight = getQuantityValueAndUnit(weight[0]);

      if (typeof systolicbp != 'undefined') {
        p.sys = systolicbp;
      } else {
        p.sys = 'undefined';
      }

      if (typeof diastolicbp != 'undefined') {
        p.dia = diastolicbp;
      } else {
        p.dia = 'undefined';
      }

      console.log("p");
      console.log(p);
      displayObservation(p);

    });



  // dummy data for medrequests
  //var medResults = ["SAMPLE Lasix 40mg","SAMPLE Naproxen sodium 220 MG Oral Tablet","SAMPLE Amoxicillin 250 MG"]

  var getPath = client.getPath;
  var rxnorm  = "http://www.nlm.nih.gov/research/umls/rxnorm";
  // var cerner = "https://fhir.cerner.com/ec2458f2-1e24-41c8-b71b-0e701af7583d/synonym";

  // get medication request resources this will need to be updated
  // the goal is to pull all the medication requests and display it in the app. It can be both active and stopped medications

  // http://docs.smarthealthit.org/client-js/request.html
  function getMedicationName(medCodings = []) {
      var rxnormCoding = medCodings.find(c => c.system === rxnorm);
      // console.log(medCodings.find(c => c.system));
      // var cernerCoding = medCodings.find(c => c.system === cerner);
      // var third = medCodings.find(c => c.system === cerner || c.system === rxnorm);
      // console.log('rxnorm coding');
      // console.log(rxnormCoding);
      // console.log('cernerCoding');
      // console.log(cernerCoding);
      // console.log('third');
      // console.log(third);
      return rxnormCoding && rxnormCoding.display; // || cernerCoding && cernerCoding.display;
  }

/*
  client.request(`/MedicationRequest?patient=${client.patient.id}`, {
      resolveReferences: "medicationReference"
  }).then(data => data.entry.map(item => getMedicationName(
      getPath(item, "resource.medicationCodeableConcept.coding") ||
      getPath(item, "resource.medicationReference.code.coding")
  ))).then(displayMedication, displayMedication);
*/

  //update function to take in text input from the app and add the note for the latest weight observation annotation
  //you should include text and the author can be set to anything of your choice. keep in mind that this data will
  // be posted to a public sandbox
  function addWeightAnnotation() {
    var annotation = document.getElementById('annotation').value;
    var anoObj = {
      "authorString" : "jobrien35", // author of note
      "time" : new Date().toISOString(),  // When the annotation was made (YYYY-MM-DDTHH:mm:ss.SSSSZ)
      "text" : annotation                 // R!  The annotation  - text content (as markdown)
    }
    // add entry not rewrite entire array
    console.log(typeof weightObs.note);
    console.log(typeof weightObs.note == 'undefined');
    if (typeof weightObs.note != 'undefined' && weightObs.note.length > 0) {
      weightObs.note.unshift(anoObj);
      console.log("prepended a new observation");
    } else {
      weightObs.note = [anoObj];
      console.log("First annotation");
    }
    console.log('anoJSON');
    console.log(anoObj);
    client.update(weightObs).then((response) => { console.log(response)});
    displayAnnotation(annotation);

  }

  // event listener when the add button is clicked to call the function that will add the note to the weight observation
  // document.getElementById('add').addEventListener('click', addWeightAnnotation);

}).catch(console.error); // fhir client end

var a = 1;
var b = null;
console.log(a);


/*
var a = fetch('./lib/fhir/Lindsey52_Ledner144_5791f6fc-11ab-e632-5fd7-3135662b1b44.json', {mode: 'cors'})
.then(data=>{return data.json()})
  .then(res=>{
    console.log(res)
    b = res;
  }).catch(err => {
  console.log(err);
});
console.log(a);
*/
