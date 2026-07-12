// how does this code work?
//   create the array
//   then grab from taht 
  
var day = document.getElementById('QuestionOptions');

console.log('hello')
 arr = [];
    for (var i = 0, l = 1000; i < 100; i++) {
    arr.push(Math.round(Math.random() * l))
    }
 
arr_1 = [];
    for (var i = 0, l = 1000; i < 100; i++) {
    arr_1.push(Math.round(Math.random() * l))
    }

day.addEventListener('change', function() {
	var QO = document.getElementById('QuestionOptions').selectedIndex;
	var val = document.getElementsByTagName("option")[QO].value;
  if(val === 'A') {
    arr = [];
    for (var i = 0, l = 1000; i < 100; i++) {
    arr.push(Math.round(Math.random() * l))
    }
    arr_1 = [];
    for (var i = 0, l = 1000; i < 100; i++) {
    arr_1.push(Math.round(Math.random() * l))
    }
    console.log(arr)
    console.log(arr_1)
    } 
  else if(val == 'B') {
    arr = [];
    for (var i = 0, l = 100; i < 100; i++) {
    arr.push(Math.round(Math.random() * l))
    }
    arr_1 = [];
    for (var i = 0, l = 100; i < 100; i++) {
    arr_1.push(Math.round(Math.random() * l))
    }
    console.log(arr)
    console.log(arr_1)
  } 
    else if(val == 'C') {
      arr = [];
    for (var i = 0, l = 10; i < 100; i++) {
    arr.push(Math.round(Math.random() * l))
    }
    arr_1 = [];
    for (var i = 0, l = 10; i < 100; i++) {
    arr_1.push(Math.round(Math.random() * l))
    }
    console.log(arr)
    console.log(arr_1)
  } 
    else if(val == 'D') {
    arr = [];
    for (var i = 0, l = 100; i < 100; i++) {
    arr.push(Math.round(Math.random() * l))
    }
    arr_1 = [11, 11];
  } 
   else if(val == 'E') {
    arr = [100];
    arr_1 = [];
    for (var i = 0, l = 100; i < 100; i++) {
    arr_1.push(Math.round(Math.random() * l))
    }
  } 
  else if(val == 'F') {
    arr = [];
    for (var i = 0, l = 100; i < 100; i++) {
    arr.push(Math.round(Math.random() * l))
    }
    arr_1 = [];
    for (var i = 0, l = 10; i < 100; i++) {
    arr_1.push(Math.round(Math.random() * l))
    }
    console.log(arr)
    console.log(arr_1)
  } 
  else {
  console.log('random placement')
  }
});



document.getElementById("targeted").focus();
 

function first(simple1) {
  space = '&nbsp;'
  var math = Math.floor( Math.random() * ( arr.length ) ) 
  text1 = arr[math]
  var math_1 = Math.floor( Math.random() * (arr_1.length ) ) 
  text2 = arr_1[math_1]
  
  // Swap text1 and text2 if text2 is larger than text1
  if (text2 > text1) {
    var temp = text1;
    text1 = text2;
    text2 = temp;
  }
  
  var math_string = math_1.toString()
  if($('#r1').is(':checked')){ 
    $("#2").text("+\xa0"+text2);
    $("#1").text("\xa0"+text1);
  } else if ($('#r2').is(':checked')) {
    $("#2").text("-\xa0"+text2);
    $("#1").text("\xa0"+text1);
  } else if ($('#r3').is(':checked')) {
    $("#2").text("*\xa0"+text2);
    $("#1").text("\xa0"+text1);
  } else if ($('#r4').is(':checked')) {
    $("#2").text("/\xa0"+text2);
    $("#1").text("\xa0"+text1);
  } else {
    console.log('none')
  }
  
  console.log($("#ptext").text())
  document.getElementById('3').innerHTML = ''
}




// change here for addition
function second(simple2) {
      if($('#r1').is(':checked')){ 
       text3 = text1 + text2;
 $("#3").text('=\xa0'+text3);
     }
     else if($('#r2').is(':checked')){ 
       text3 = text1 - text2;
 $("#3").text('=\xa0'+text3);
     }
      else if($('#r3').is(':checked')){ 
       text3 = text1 * text2;
 $("#3").text('=\xa0'+text3);
     }
        else if($('#r4').is(':checked')){ 
       text3 = text1 / text2;
 $("#3").text('=\xa0'+text3);
     }
  else {
   console.log('none')
  }
  console.log($("#3").text())
}

//why do I need this reload?
// function myFunction3() {
//     window.location.reload(true);
// }




  // var newtext = document.createTextNode(text2+"     "),
  //     p2 = document.getElementById("p2");

//   p2.appendChild(newtext);






// function addTextNode2(simple3) {
//   text3 = text2 + text1
//   var newtext1 = document.createTextNode(text3),
//       p3 = document.getElementById("p3");

//   p3.appendChild(newtext1);
// }




// function addTextNode4() {
//     if (text1 > text2){
//     text3 = text1 - text2;
//     var newtext4 = document.createTextNode(text3),
//       p3 = document.getElementById("p3");}
//     else if(text2 > text1){
//     text3 = text2 - text1;");}
//     var newtext4 = document.createTextNode(text3),
//       p3 = document.getElementById("p3
//      p3.appendChild(newtext4);
// }

// function test(sampleplace1){ 
//   if(text1 > text2){ 
//       q = text1 - text2; 
//       var storm = document.createTextNode(q).value,
//       p1 = document.getElementById("p1");} 
//       else if(text2 > text1){ 
//         z = text2 - text1; 
//       var storm = document.createTextNode(z).value,
//       p1 = document.getElementById("p1");
//      } 
//     p1.appendChild(storm);
// }


// Get the buttons and the percentage display
// Get the buttons and the percentage display
const rightBtn = document.getElementById("rightBtn");
const wrongBtn = document.getElementById("wrongBtn");
const percentageDisplay = document.getElementById("percentage");
const rightAnswersDisplay = document.getElementById("rightAnswers");

// Initialize the variables
let totalQuestions = 0;
let rightAnswers = 0;

// Add event listeners to the buttons
rightBtn.addEventListener("click", () => {
  totalQuestions++;
  rightAnswers++;
  updatePercentage();
});

wrongBtn.addEventListener("click", () => {
  totalQuestions++;
  updatePercentage();
});

// Function to calculate and update the percentage and right answers
function updatePercentage() {
  const percentage = ((rightAnswers / totalQuestions) * 100).toFixed(0);
  const rightAnswersText = `Right Answers: ${rightAnswers} out of ${totalQuestions}`;
  percentageDisplay.textContent = `${percentage}%`;
  rightAnswersDisplay.textContent = rightAnswersText;
}

$(document).on("keypress", function (e) {
  if (e.which == 113) { // "q" key maps to keycode `113`
    first('Hi from Q');
    console.log('hi from Q');
  } else if (e.keyCode == 119) { // space key maps to keycode `27`
    second('no');
       console.log('bye')
  } else if (e.which == 49) { // "1" key maps to keycode `49`
    totalQuestions++;
    rightAnswers++;
    updatePercentage();
    console.log('hi from 1');
  } else if (e.which == 50) { // "2" key maps to keycode `50`
    totalQuestions++;
    updatePercentage();
  }

});


function addDate() {
        // Get current date
        let currentDate = new Date();
        // Format date as mm-dd-yyyy
        let formattedDate = (currentDate.getMonth() + 1).toString().padStart(2, '0') + '-' + currentDate.getDate().toString().padStart(2, '0') + '-' + currentDate.getFullYear().toString();
        // Get reference to textarea
        let textarea = document.getElementById('myTextarea');
        // Append date to textarea separated by comma
  // Get character count
  let characterCount = textarea.value.length;
  // Append date to textarea separated by comma
  if (characterCount > 0) {
    textarea.value += '\n' + formattedDate + ', ';
  } else {
    textarea.value += formattedDate + ', ';
  }
      }


const addDateBtn = document.getElementById("addDateBtn")
addDateBtn.addEventListener("click", () => {
  addDate();
});


   function addTime() {
        // Get current time
        let currentTime = new Date();
        // Format time as hh:mm a
        let formattedTime = currentTime.toLocaleTimeString('en-US', {hour: 'numeric', minute: 'numeric', hour12: true});
        // Get reference to textarea
        let textarea = document.getElementById('myTextarea');
        // Append time to textarea separated by comma
        textarea.value += formattedTime + ', ';
      }


const addTimeBtn = document.getElementById("addTimeBtn")
addTimeBtn.addEventListener("click", () => {
  addTime();
});

const dropdownMenu = document.getElementById("dropdownMenu");

dropdownMenu.addEventListener("change", () => {
  const selectedOption = dropdownMenu.options[dropdownMenu.selectedIndex];
  if (selectedOption) {
    myTextarea.value += selectedOption.value.charAt(0).toUpperCase() + selectedOption.value.slice(1) + ", ";    // Reset dropdown to default option
    dropdownMenu.selectedIndex = 0;
  }
});
let minutes = 25;
let seconds = 0;
let timer;
let timerRunning = false;

function updateTimer() {
  // Update the timer display
  document.getElementById("minutes").innerHTML = minutes.toString().padStart(2, "0");
  document.getElementById("seconds").innerHTML = seconds.toString().padStart(2, "0");

  // Change the title of the webpage as the timer counts down
  document.title = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")} - Pomodoro Timer`;

  // Check if the timer has reached 0
  if (minutes === 0 && seconds === 0) {
    clearInterval(timer);
    document.title = "Time's up! - Pomodoro Timer";
    var now = new Date();
var timeString = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

alert("Time's up at" + timeString);

    timerRunning = false;
  } else {
    // Decrease the time by one second
    if (seconds === 0) {
      minutes--;
      seconds = 59;
    } else {
      seconds--;
    }
  }
}

function startTimer() {
  if (!timerRunning) {
    // Start the timer
    timer = setInterval(updateTimer, 1000);
    timerRunning = true;
  }
}

function stopTimer() {
  if (timerRunning) {
    // Stop the timer
    console.log("Stopping timer");
    clearInterval(timer);
    console.log("Timer stopped");
    minutes = 0;
    seconds = 1;
    updateTimer();
    document.title = "Pomodoro Timer";
    timerRunning = false;
  }
}

function resetTimer() {
  // Reset the timer
  clearInterval(timer);
  minutes = 25;
  seconds = 0;
  updateTimer();
  document.title = "Pomodoro Timer";
  timerRunning = false;
}

let minutes1 = 5;
let seconds1 = 0;
let timer1;

function updateTimer1() {
  // Update the timer display
  document.getElementById("minutes1").innerHTML = minutes1.toString().padStart(2, "0");
  document.getElementById("seconds1").innerHTML = seconds1.toString().padStart(2, "0");

  // Change the title of the webpage as the timer counts down
  document.title = `${minutes1.toString().padStart(2, "0")}:${seconds1.toString().padStart(2, "0")} - Pomodoro Timer`;

  // Check if the timer has reached 0
  if (minutes1 === 0 && seconds1 === 0) {
    clearInterval(timer1);
    document.title = "Time's up! - Pomodoro Timer";
    var now = new Date();
var timeString = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

alert("Time's up at " + timeString);


  } else {
    // Decrease the time by one second
    if (seconds1 === 0) {
      minutes1--;
      seconds1 = 59;
    } else {
      seconds1--;
    }
  }
}

function startTimer1() {
  if (!timerRunning) { // check if timer is not already running
    // Start the timer
    timer1 = setInterval(updateTimer1, 1000);
    timerRunning = true;
  }
}

function stopTimer1() {
  // Stop the timer
  console.log("Stopping timer");
  clearInterval(timer1);
  console.log("Timer stopped");
  minutes1 = 0;
  seconds1 = 1;
  updateTimer1();
  document.title = "Pomodoro Timer";
  timerRunning = false;
}

function resetTimer1() {
  // Reset the timer
  clearInterval(timer1);
  minutes1 = 5;
  seconds1 = 0;
  updateTimer1();
  document.title = "Pomodoro Timer";
  timerRunning = false;
}

const makeTableButton = document.getElementById('makeTable');

function makeTable() {
  let textAreaValue = document.getElementById("myTextarea").value;

  if (!textAreaValue.includes('\n')) {
    // Get the value from the text area
    let textAreaValue = document.getElementById("myTextarea").value;

    // Split the value by comma and store the values in an array
    let valuesArray = textAreaValue.split(",");

    // Create a table element
    let table = document.createElement("table");

    // Create a table row for the table headers
    let tableHeaderRow = document.createElement("tr");

  // Create the table headers and append them to the table header row
    let headers = ["Date", "Start Time", "End Time", "Duration"];
    for (let i = 0; i < headers.length; i++) {
      let header = document.createElement("th");
      header.textContent = headers[i];
      tableHeaderRow.appendChild(header);
    }

    // Append the table header row to the table element
    //table.appendChild(tableHeaderRow);

    // Create a table row for the values
    let tableRow = document.createElement("tr");

    // Loop through the values array and create table cells for each value
    for (let i = 0; i < valuesArray.length; i++) {
      let cell = document.createElement("td");
      cell.textContent = valuesArray[i];
      tableRow.appendChild(cell);
    }

    // Append the table row to the table element
    table.appendChild(tableRow);


    // Get the div element with the id "new_table"
    let tableDiv = document.getElementById("new_table");

    // Append the table element to the tableDiv
    tableDiv.appendChild(table);

    } else {
      // Get the value from the text area
      let textAreaValue = document.getElementById("myTextarea").value;

      // Split the value by newline and store the rows in an array
      let rowsArray = textAreaValue.split("\n");

      // Create a table element
      let table = document.createElement("table");

      // Create a table row for the table headers
      let tableHeaderRow = document.createElement("tr");

      // Create the table headers and append them to the table header row
      let headers = ["Date", "Start Time", "End Time", "Duration"];
      for (let i = 0; i < headers.length; i++) {
        let header = document.createElement("th");
        header.textContent = headers[i];
        tableHeaderRow.appendChild(header);
      }

      // Append the table header row to the table element
      //table.appendChild(tableHeaderRow);

      // Loop through the rows array and create table rows for each row of values
      for (let i = 0; i < rowsArray.length; i++) {
        // Split the row by comma and store the values in an array
        let valuesArray = rowsArray[i].split(",");

        // Create a table row for the values
        let tableRow = document.createElement("tr");

        // Loop through the values array and create table cells for each value
        for (let j = 0; j < valuesArray.length; j++) {
          let cell = document.createElement("td");
          cell.textContent = valuesArray[j];
          tableRow.appendChild(cell);
        }

        // Append the table row to the table element
        table.appendChild(tableRow);
      }
          let tableDiv = document.getElementById("new_table");

    // Append the table element to the tableDiv
    tableDiv.appendChild(table);
    }
        // Get the div element with the id "new_table"

    }


makeTableButton.addEventListener('click', () => {
  makeTable();
  const table = document.getElementById('new_table');
  const tableText = table.innerText;
  navigator.clipboard.writeText(tableText)
    .then(() => {
      console.log('Table contents copied to clipboard!');
    let tableDiv = document.getElementById("new_table");

        // Append the table element to the tableDiv   
   tableDiv.innerHTML += 'copied to the clipboard!';
    })
    .catch((error) => {
      console.error('Error copying table contents to clipboard: ', error);
    });
          
});

 function playAudio() {
    var audio = document.getElementById("myAudio");
    audio.play();
  }