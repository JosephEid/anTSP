/**
 * solve - Solves an instance specified by the user, this is done through the
 * use of a GET AJAX request.
 *
 */
function solve() {

  // Empty the console and disable the solve button.
  $("#messages").empty()
  $("#solveButton").attr("disabled", true);

  // Extract the form data
  var form_alpha = document.forms["myForm"]["alpha"].value;
  var form_generations = document.forms["myForm"]["generations"].value;
  var form_instance = document.forms["myForm"]["instance"].value;
  var form_beta = document.forms["myForm"]["beta"].value;
  var form_pec = document.forms["myForm"]["pec"].value;
  var form_q = document.forms["myForm"]["q"].value;

  // Start the run-time timer/
  var start = new Date().getTime();
  $('#timeStart').empty();
  $('#timeStart').append(start);

  // If the instance is a custom one, do not plot the optimal as it does not exist
  // set the AJAX URL as /createcustom. If its not a custom instance, set the
  // AJAX URL as /createinstance and plot the optimal graph.
  if (form_instance == "Custom"){
    coords = $("#savedCustomCoords").text();
    getURL = "/createcustom.png?alpha="+form_alpha+"&generations="+form_generations+
      "&beta="+form_beta+"&custom_coords="+coords+"&pec="+form_pec+"&q="+form_q;
  }
  else {
    img2 = document.getElementById("graph2");
    // SocketIO client ID to ensure only they see the appropriate console messages
    client = $("#clientId").text();
    img2.src="/plotoptimum.png?prev_instance="+form_instance+"&client="+client;
    getURL = "/createinstance?alpha="+form_alpha+"&beta="+form_beta+"&instance="+form_instance+"&pec="+form_pec+"&q="+form_q;
  }

  // AJAX Request
  $.ajax({
      url: getURL,
      type: "GET",
      success: function(data) {
        console.log(data);
        add(data.message).prependTo('#messages');
        client = $("#clientId").text();
        // Start the algorithm on the instance
        doGenerations(data, form_generations, 1, form_instance, client);

      },
      error: function(error) {
          console.log(error);
      }
  });
}


/**
 * doGenerations - communicates with the server to start the algorithm on the
 * instance. Plots the graph once complete.
 *
 * @param graph_data The instance graph data
 * @param gens       The generations specified by the user
 * @param currentGen The generation reached so far
 * @param instance   The name of the instance being solved
 * @param client     The client ID to enable SocketIO communications
 */
function doGenerations(graph_data, gens, currentGen, instance, client) {
  // Parse the total generations and current generation
  gens = parseInt(gens);
  currentGen = parseInt(currentGen)
  // Post request to perform generations on current Instance
  $.ajax({
      url: "/dogen?gens="+gens+"&currentGen="+currentGen+"&client="+client,
      type: "POST",
      data: JSON.stringify(graph_data),
      contentType: "application/json",
      success: function(response) {
        // Display message to console
        add(response.message).prependTo('#messages');

        // If specified number of generations are reached, plot the graph.
        if (response.gen_reached == gens) {
          var now = new Date().getTime();
          start = $('#timeStart').text();
          optDist = $('#optDist').text();
          optDist = parseFloat(optDist);
          plotGraph(instance, response.shortest_path, response.min_distance);

          error = 100 - 100*(optDist/parseFloat(response.min_distance));
          add("Percentage error: " + (1*error) + "% run-time: " + (now-start)/1000 + "s").prependTo('#messages');


          $('#solveButton').attr("disabled", false);
        }
        else {
          // If generation has run longer than 25 seconds, recursively call Generations
          // again.
          currentGen = response.gen_reached
          doGenerations(response, gens, currentGen, instance, client);
        }
      },
      error: function(error) {
          console.log(error);
      }
  });
}


/**
 * plotGraph - Plots the final solution as a graph
 *
 * @param instance The instance name
 * @param path     The shortest path found
 * @param distance The minimum distance found
 */
function plotGraph(instance, path, distance) {
  img = document.getElementById("graph1");
  if (instance == "Custom") {
    // Extract the custom coords
    coords = $("#savedCustomCoords").text();
    img.src="/plotGraph.png?instance="+instance+"&path="+path+"&distance="+distance+"&coords="+coords;
  }
  else {
    img.src="/plotGraph.png?instance="+instance+"&path="+path+"&distance="+distance;
  }
}


/**
 * previewInstance - If the user selects an instance from the dropdown list on the form
 * previews the instance nodes as a graph.
 *
 */
function previewInstance() {
  // Get the instance name from the form
  var form_instance = document.forms["myForm"]["instance"].value;
  if (form_instance == "Custom"){
    coords = $("#savedCustomCoords").text()
    img1 = document.getElementById("graph1");
    img1.src="/custompreview.png?custom_coords="+coords;
  }
  else {
    image = "/plotpreview.png?prev_instance="+form_instance;
    img1 = document.getElementById("graph1");
    img1.src = image;
    // Plot the preview on the optimal too
    img2 = document.getElementById("graph2");
    img2.src = image;
  }

}


/**
 * addCoordinate - adds a user inputted coordinate if it is not a duplicate node.
 *
 */
function addCoordinate() {
  // Extract the x and y values.
  var x_val = document.forms["customForm"]["xVal"].value;
  var y_val = document.forms["customForm"]["yVal"].value;


  customCoords = document.forms["customForm"]["customCoords"];
  coords = $("#customCoords").text();
  currentNodes = coords.split(':')
  var node = "("+x_val+","+y_val+")";

  // Check that the node does not already exist
  if (!currentNodes.includes(node)) {
    console.log("good");
    customCoords.append(node+":");
    coords = $("#customCoords").text();
    img = document.getElementById("graphCustom");
    img.src="/custompreview.png?custom_coords="+coords;
  }
  else {
    console.log("bad");
    $("#errors").empty();
    $("#errors").val("Duplicate node").html("Duplicate node");
  }

}


/**
 * saveChanges - saves the custom instance
 *
 */
function saveChanges() {
  // Empty the previous custom coordinates
  $("#savedCustomCoords").empty();
  // Checks how many custom nodes exist
  customCoords = document.forms["customForm"]["customCoords"];
  coords = $("#customCoords").text();
  num = coords.split(':').length-1;
  // If there is more than 1 unique coordinate, save is successful
  if (num > 1) {
    savedCustomCoords = document.forms["myForm"]["savedCustomCoords"];
    savedCustomCoords.append(coords);
    var form_instance = document.forms["myForm"]["instance"].value;
    $('#customModal').modal('hide')
    if (form_instance == "Custom"){
      previewInstance();
    }
  }
  else {
    // show the user an error
    $("#errors").empty();
    $("#errors").val("Not enough nodes").html("An instance should contain a minimum of 2 nodes");
  }
}


/**
 * resetCustom - clears the custom instance
 *
 */
function resetCustom() {
  $("#customCoords").empty()
  img = document.getElementById("graphCustom");
  img.src="/custompreview.png?custom_coords=''";
}


/**
 * add - adds messages to a list element to be appended to the console on the webpage.
 *
 * @param  {type} message message to be appended to console
 */
function add(message) {
  var text = $('<span class="message">').text(message);
  text.html(message);
  var t = $('<li>');
  t.append(text);
  return t;
}
