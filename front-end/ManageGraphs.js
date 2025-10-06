// 

	console.log("entering manage graph module");
	var index1 = 0;
	var newdata = {
		Tcabin:1,
		Tevap:2,
		BlowSpeed:3
	};  
	
	var config = {
		type: 'line',
		data: {
			labels: [0],
			datasets: [{
				label: 'Cabin Temp',
				backgroundColor: window.chartColors.red,
				borderColor: window.chartColors.red,
				data: [
					0					
				],
				fill: false,
			}, {
				label: 'Evap Temp',
				fill: false,
				backgroundColor: window.chartColors.blue,
				borderColor: window.chartColors.blue,
				data: [
					0
				],
			}]
		},
		options: {
			responsive: true,
			title: {
				display: true,
				text: 'Temperatures'
			},
			tooltips: {
				mode: 'index',
				intersect: false,
			},
			hover: {
				mode: 'nearest',
				intersect: true
			},
			scales: {
				xAxes: [{
					display: true,
					scaleLabel: {
						display: true,
						labelString: 'Time'
					}
				}],
				yAxes: [{
					display: true,
					scaleLabel: {
						display: true,
						labelString: 'Value'
					}
				}]
			}
		}
	};
	
	var configblower = {
		type: 'line',
		data: {
			labels: [0],
			datasets: [{
				label: 'Blower Speed',
				backgroundColor: window.chartColors.green,
				borderColor: window.chartColors.green,
				data: [
					0					
				],
				fill: false,
			}]
		},
		options: {
			responsive: true,
			title: {
				display: true,
				text: 'Blower Speed'
			},
			tooltips: {
				mode: 'index',
				intersect: false,
			},
			hover: {
				mode: 'nearest',
				intersect: true
			},
			scales: {
				xAxes: [{
					display: true,
					scaleLabel: {
						display: true,
						labelString: 'Time'
					}
				}],
				yAxes: [{
					display: true,
					scaleLabel: {
						display: true,
						labelString: 'Value'
					}
				}]
			}
		}
	};

	window.onload = function() {
		var ctx = document.getElementById('myChart').getContext('2d');
		window.myLine = new Chart(ctx, config);
		var ctx2 = document.getElementById('BlowerChart').getContext('2d');
		window.myLineBlower = new Chart(ctx2, configblower);
	};

	function UpdateGraphs() {
		console.log('update graphs');
		config.data.labels.push(index1);
		index1++;
		config.data.datasets[0].data.push(newdata.Tcabin);
		config.data.datasets[1].data.push(newdata.Tevap);
		configblower.data.labels.push(index1);
		configblower.data.datasets[0].data.push(newdata.BlowSpeed);
		
		newdata = {
		Tcabin:999,
		Tevap:999,
		BlowSpeed:999};

		window.myLine.update();
		window.myLineBlower.update();
				
	}
		