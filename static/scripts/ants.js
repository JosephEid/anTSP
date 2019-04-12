function solve() {
  var form_alpha = document.forms["myForm"]["alpha"].value;
  var form_generations = document.forms["myForm"]["generations"].value;
  var form_instance = document.forms["myForm"]["instance"].value;
  var form_beta = document.forms["myForm"]["beta"].value;
  var form_pec = document.forms["myForm"]["pec"].value;
  var form_q = document.forms["myForm"]["q"].value;
  if (form_instance == "Custom"){
    console.log("here son");
    coords = $("#savedCustomCoords").text()
    img1 = document.getElementById("graph1");
    img1.src="/plotcustom.png?alpha="+form_alpha+"&generations="+form_generations+
    "&beta="+form_beta+"&custom_coords="+coords+"&pec="+form_pec+"&q="+form_q;
  }
  else {
    img = document.getElementById("graph1");
    img.src="/plot.png?alpha="+form_alpha+"&generations="+form_generations+
    "&beta="+form_beta+"&instance="+form_instance+"&pec="+form_pec+"&q="+form_q;
  }

  dist ="/plotDistance";
  $("#tourDistance").text(dist)
}

function previewInstance() {
  var form_instance = document.forms["myForm"]["instance"].value;
  console.log(form_instance);
  if (form_instance == "Custom"){
    coords = $("#savedCustomCoords").text()
    img1 = document.getElementById("graph1");
    img1.src="/custompreview.png?custom_coords="+coords;
  }
  else {
    img1 = document.getElementById("graph1");
    img1.src="/plotpreview.png?prev_instance="+form_instance;
    img2 = document.getElementById("graph2");
    img2.src="/plotoptimum.png?prev_instance="+form_instance;
  }

}

function addCoordinate() {
  var x_val = document.forms["customForm"]["xVal"].value;
  var y_val = document.forms["customForm"]["yVal"].value;

  customCoords = document.forms["customForm"]["customCoords"];
  customCoords.append("("+x_val+","+y_val+"):");
  coords = $("#customCoords").text();
  img = document.getElementById("graphCustom");
  img.src="/custompreview.png?custom_coords="+coords;
}

function saveChanges() {
  $("#savedCustomCoords").empty();
  customCoords = document.forms["customForm"]["customCoords"];
  console.log(customCoords);
  coords = $("#customCoords").text();
  savedCustomCoords = document.forms["myForm"]["savedCustomCoords"];
  savedCustomCoords.append(coords);
  console.log($("#savedCustomCoords").text());
  var form_instance = document.forms["myForm"]["instance"].value;
  console.log(form_instance);
  if (form_instance == "Custom"){
    previewInstance();
  }
}

function resetCustom() {
  $("#customCoords").empty()
  img = document.getElementById("graphCustom");
  img.src="/custompreview.png?custom_coords=''";
}
