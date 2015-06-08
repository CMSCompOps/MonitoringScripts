function makeChart(chartData, chartType, chartRotate, valueField, chartLocation, db)
 	{
		var rotate = false;
     	if (chartRotate == 'false') {rotate = false} else {rotate = true;}
     	switch(valueField){
			case "Days":
				str = " day(s)";
				break;
			case "average":
				str = "%";
				break;
			case "number":
				str = " Number";
				break;
		}	


if (db == 'links'){
 var chartSum5 = AmCharts.makeChart(chartLocation, {
                type: "serial",
                dataProvider: chartData,
                categoryField: "errorname",
    	        depth3D : 0,
	            angle : 15,
                rotate: true,
                startDuration : 1,
         
                categoryAxis: {
                    labelRotation: 0,
                    gridPosition: "start",
                    autoGridCount: false,
                    gridCount : chartData.length,
                },

                valueAxes: [{
                    title: (valueField == "Days") ? "Day(s)" : (valueField == "average") ? "Average Site Readiness (%)" : "The Number of times",
                }],

                graphs: [{
                    type: "column",
                    lineAlpha: 10,
                    fillAlphas: 10,
                    lineThickness: 2,
                    columnWidth: 1,
					balloonText : (valueField == "Days") ? "<b>[[value]]</b>" : (valueField == "average") ? "<b>[[value]]%</b>" : "[[value]] times",
                    valueField: "errorcountgF",
                    colorField: "color",
                    title: "Good T2 links from T1s",
                },{

                    type: "column",
                    lineAlpha: 10,
                    fillAlphas: 10,
                    lineThickness: 2,
                    columnWidth: 1,
					balloonText : (valueField == "Days") ? "<b>[[value]]</b>" : (valueField == "average") ? "<b>[[value]]%</b>" : "[[value]] times",
                    valueField: "errorcountgT",
                    colorField: "color",
                    title: "Good T2 links to T1s",
                },
                
                {
                    type: "column",
                    lineAlpha: 10,
                    fillAlphas: 10,
                    lineThickness: 2,
                    columnWidth: 1,
					balloonText : (valueField == "Days") ? "Day(s):<b>[[value]]</b>" : (valueField == "average") ? "[[category]] :<b>[[value]]%</b>" : "[[value]] times",
                    valueField: "errorcountaF",
                    colorField: "color",
                    title: "Active T2 links from T1s",
                },
                
                {
                    type: "column",
                    lineAlpha: 10,
                    fillAlphas: 10,
                    lineThickness: 2,
					balloonText : (valueField == "Days") ? "Day(s):<b>[[value]]</b>" : (valueField == "average") ? "<b>[[value]]%</b>" : "[[value]] times",
                    valueField: "errorcountaT",
                    colorField: "color",
                    title: "Good T2 links to T1s",
                },

                
                ],

                chartCursor: {
                    cursorAlpha : 1,
                    zoomable: false,
                    categoryBalloonEnabled: true
                },

                    legend: {
                    align: "center",
                    markerType: "circle",
//                    valueText : "[[value]] Day(s)",
					valueText : (valueField == "Days") ? "[[value]] Day(s)" : "[[value]] times" 
                },
   


                exportConfig: {
                    menuTop: "21px",
                    menuBottom: "auto",
                    menuRight: "21px",
                    backgroundColor: "transparent",

                    menuItemStyle	: {
                    backgroundColor			: 'transparent',
                    rollOverBackgroundColor	: '#DDDDDD'},

                    menuItems: [{
                        textAlign: 'center',
                        icon: 'amcharts/images/export.png',
                        onclick:function(){},
                        items: [{
                            title: 'JPG',
                            format: 'jpg'
                        }, {
                            title: 'PNG',
                            format: 'png'
                        }, {
                            title: 'SVG',
                            format: 'svg'
                        }, {
                            title: 'PDF',
                            format: 'pdf'
                        }]
                    }]
                }
            });
            
}else{

 	if (chartType == 'pie'){
 		chart2 = AmCharts.makeChart(chartLocation, {
                type: "pie",
                dataProvider: chartData,
                titleField: "siteName",
                valueField: valueField,
                balloonText : (valueField == "Days") ? "<b>[[value]] day(s)</b> ([[percents]]%)" : "<b>[[value]] times</b> ([[percents]]%)", 

    	        depth3D : 15,
	            angle : 30,
				legend: {
                    align: "center",
                    markerType: "circle",
//                    valueText : "[[value]] Day(s)",
					valueText : (valueField == "Days") ? "[[value]] Day(s)" : "[[value]] times" 
					
                    
                },
                
                exportConfig: {
                menuTop: "21px",
                menuBottom: "auto",
                menuRight: "21px",
                backgroundColor: "transparent",

                menuItemStyle	: {
                backgroundColor			: 'transparent',
                rollOverBackgroundColor	: '#DDDDDD'},

                menuItems: [{
                    textAlign: 'center',
                    icon: 'amcharts/images/export.png',
                    onclick:function(){},
                    items: [{
                        title: 'JPG',
                        format: 'jpg'
                    }, {
                        title: 'PNG',
                        format: 'png'
                    }, {
                        title: 'SVG',
                        format: 'svg'
                    }, {
                        title: 'PDF',
                        format: 'pdf'
                    }]
                }]
            }

                
                
            });
	}; //end of if
 
  if (chartType == 'bar'){
        var chartSum1 = AmCharts.makeChart(chartLocation, {
                type: "serial",
                dataProvider: chartData,
                categoryField: "siteName",
    	        depth3D : 0,
	            angle : 15,
                rotate: rotate,
                startDuration : 1,
         
                categoryAxis: {
                    labelRotation: 90,
                    gridPosition: "start",
                    autoGridCount: false,
                    gridCount : chartData.length,
                },

                valueAxes: [{
                    title: (valueField == "Days") ? "Day(s)" : (valueField == "average") ? "Average Site Readiness (%)" : "The Number of times",
                }],

                graphs: [{
                   // balloonText: (valueField == 'average') ? "[[category]] :<b>[[value]]%</b>" : "[[category]]\'s number of [[title]] :<b>[[value]]</b>",
                    
					balloonText : (valueField == "Days") ? "Day(s):<b>[[value]]</b>" : (valueField == "average") ? "<b>[[value]]%</b>" : "[[value]] times",
                    valueField: valueField,
                    colorField: "color",
                    type: "column",
                    lineAlpha: 0,
                    fillAlphas: 1,
                    lineColor : "#8cc218",
                }],

                chartCursor: {
                    cursorAlpha : 1,
                    zoomable: false,
                    categoryBalloonEnabled: true
                },

                exportConfig: {
                    menuTop: "21px",
                    menuBottom: "auto",
                    menuRight: "21px",
                    backgroundColor: "transparent",

                    menuItemStyle	: {
                    backgroundColor			: 'transparent',
                    rollOverBackgroundColor	: '#DDDDDD'},

                    menuItems: [{
                        textAlign: 'center',
                        icon: 'amcharts/images/export.png',
                        onclick:function(){},
                        items: [{
                            title: 'JPG',
                            format: 'jpg'
                        }, {
                            title: 'PNG',
                            format: 'png'
                        }, {
                            title: 'SVG',
                            format: 'svg'
                        }, {
                            title: 'PDF',
                            format: 'pdf'
                        }]
                    }]
                }
            });
	} // end of if
 
    if (chartType == 'line'){
        var chartSum3 = AmCharts.makeChart(chartLocation, {
                type: "serial",
                dataProvider: chartData,
                categoryField: "siteName",
                depth3D: 0,
                angle: 30,
                rotate: rotate,
                startDuration : 1,

         
                categoryAxis: {
                    labelRotation: 90,
                    gridPosition: "start"
                },

                valueAxes: [{
                    title: (valueField == "Days") ? "Day(s)" : (valueField == "average") ? "Average Site Readiness (%)" : "The Number of times",
                }],

                graphs: [{
					type: "line",
                    title: "Days",
                    valueField: valueField,
                    lineThickness: 2,
                    fillAlphas: 0.4,
                    lineColor : "#1fa0d6",
                    bullet: "round",
					balloonText : (valueField == "Days") ? "Day(s):<b>[[value]]</b>" : (valueField == "average") ? "<b>[[value]]%</b>" : "[[value]] times",

                }],

                chartCursor: {
                    cursorAlpha : 1,
                    zoomable: false,
                    categoryBalloonEnabled: true
                },

                exportConfig: {
                    menuTop: "21px",
                    menuBottom: "auto",
                    menuRight: "21px",
                    backgroundColor: "transparent",

                    menuItemStyle	: {
                    backgroundColor			: 'transparent',
                    rollOverBackgroundColor	: '#DDDDDD'},

                    menuItems: [{
                        textAlign: 'center',
                        icon: 'amcharts/images/export.png',
                        onclick:function(){},
                        items: [{
                            title: 'JPG',
                            format: 'jpg'
                        }, {
                            title: 'PNG',
                            format: 'png'
                        }, {
                            title: 'SVG',
                            format: 'svg'
                        }, {
                            title: 'PDF',
                            format: 'pdf'
                        }]
                    }]
                }
            });
	} // end of if
  }
}
