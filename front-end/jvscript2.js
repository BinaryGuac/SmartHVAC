// java script for simple demo using paho-mqtt.js

var disconnectiontime = 0;
var    connectiontime = 0;
var connectimeinterval = 1000;
var undeliveredMessages = []
console.log('START of script exec');

var client = new Paho.MQTT.Client("m11.cloudmqtt.com",37334,'', "frocha@bergstrominc.com");
client.onMessageArrived = onMessageArrived;
//client.onMessageDelivered = onMessageDelivered;

var options = {
				useSSL:true,
                userName: "kyfylcvw",
                password: "X-vhsAL9DNBD",
                onSuccess: onConnect,
				onFailure: doFail
};


  // connect the client
  console.log('Log-Connection');
  //client.connect(options);
  console.log(client.isConnected())

  // called when the client connects
  function onConnect() {
    // Once a connection has been made, make a subscription and send a message.
    console.log("Log-onConnect");
	client.subscribe('log', {qos: 2}); // could be done later but it seems to create a connection issue later if not done at this step!
    message = new Paho.MQTT.Message("Remote Client Connected");
    message.destinationName = "log";
    client.send(message);
  }

  function doFail(e){
    console.log('Connection error');
  }

  // called when the client loses its connection
  function onConnectionLost(responseObject) {
    if (responseObject.errorCode !== 0) {
      console.log("onConnectionLost:"+responseObject.errorMessage);
    }
  }

  // called when a message arrives
  function onMessageArrived(message) {
		var payload = "";
		var topic = "";
		topic = message.destinationName; //message._getDestinationName.arguments;
		payload = message.payloadString;
		console.log("onMessageArrived: "+ message.destinationName + "  " + message.payloadString);
		switch(topic){
			case "EvapTemp":
				document.getElementById('evaptemp').value = payload;
				newdata.Tevap = parseFloat(payload);
				console.log(newdata.Tevap);
				break;
			case "AmbTemp":
				document.getElementById('ambtemp').value = payload;
				break;
			case "CabTemp":
				document.getElementById('cabtemp').value = payload;
				newdata.Tcabin = parseFloat(payload);
				console.log(newdata.Tcabin);				
				break;
			case "blowerspeed":
				document.getElementById('blowspeed').value = payload;
				newdata.BlowSpeed = parseFloat(payload);
				console.log(newdata.BlowSpeed);				
				break;
			case "error":
				document.getElementById('errorcode').value = payload;
				break;					
			case "log":
				document.getElementById('log').value = payload;
				break;				
			default:
				document.getElementById('log').value = topic + " : " + payload;
		}
		
		if ((newdata.Tcabin<999)&&(newdata.Tevap<999)&&(newdata.BlowSpeed<999)){
			UpdateGraphs();
		}


	}
  
   // called when a publish button is presssed
  function publish(message) {
		var x = document.getElementById('onoffreq').value
		var y = document.getElementById('setpointreq').value
		var z = document.getElementById('blowreq').value
		console.log("Going to publish this value:" + x + y + z);
		client.publish('OnOff',x);
		client.publish('setpoint',y);
		client.publish('blowerspeedreq',z);
		client.publish('log','Command sent by web user');
	
  }
  
  function SubscribeTopic(topic) {
		client.subscribe('EvapTemp', {qos: 2}); 
		client.subscribe('CabTemp', {qos: 2}); 
		client.subscribe('AmbTemp', {qos: 2}); 
		client.subscribe('blowerspeed', {qos: 2}); 
		client.subscribe('error', {qos: 2});
		client.subscribe('log', {qos: 2}); 
		
  }
  
  	// create a counter at the bottom of the page
	var myVar = setInterval(myTimer, 1000);
	function myTimer() {
		var d = new Date();
		document.getElementById("counter").innerHTML = "TIME: " + d.toLocaleTimeString();
	}
	var timer2 = setInterval(myTimer2, connectimeinterval);
	function myTimer2() {
		console.log("Connection is " + client.isConnected());
		if  (client.isConnected() == true) {
		document.getElementById("ConnectionSts").innerHTML = "Connection Status: " + "Connected for " + connectiontime + " seconds";
		document.getElementById("ConnectionSts").style="color:green;"
		disconnectiontime = 0;
		}
		else {
			document.getElementById("ConnectionSts").innerHTML = "Connection Status: " + "MQTT Broker Disconnected for " + disconnectiontime + " seconds";
			document.getElementById("ConnectionSts").style="color:Red;"
			connectiontime = 0;
		}
		connectiontime +=connectimeinterval/1000;
		disconnectiontime +=connectimeinterval/1000;
	}