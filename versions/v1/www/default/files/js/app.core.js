
Object.byString = function(o, s) {
	s = s.replace(/\[(\w+)\]/g, '.$1'); // convert indexes to properties
	s = s.replace(/^\./, '');           // strip a leading dot
	var a = s.split('.');
	for (var i = 0, n = a.length; i < n; ++i) {
		var k = a[i];
		try {
			if (k in o) {
				o = o[k];
			} else {
				return;
			}
		}
		catch (err) {
			return;
		}
	}
	return o;
};


Hashtable = function(retNoString) {
	if ((retNoString==null) || (retNoString=='undefined')) retNoString = false;
	this.init(retNoString);
};

$.extend(Hashtable.prototype, {
		 array : new Array(),
		 retString : false,
		 __keys : null,
		 init : function(retNoString) {
			 this.retString = retNoString;
			 this.clear();
		 },
		 count : function() {
			 return this.array.length;
		 },
		 pop : function() {
			 var top = this.array.pop();
			 this.__keys = null;
			 return top.value;
		 },
		 clear : function() {
			 this.array = null; // force garbage collection...
			 this.array = new Array();
			 this.__keys = null;
		 },
		 exists : function(key) {
			 return (this.indexof(key) !=-1);
		 },
		 indexof : function(key) {
			 return $.inArray(key, this.keys());
		 },
		 itemat : function(index) {
			 if ((index >= 0) && (index < this.array.length)) {
				 return this.array[index].value;
			 }
			 return null;
		 },
		 rawat : function(index) {
			 if ((index >= 0) && (index < this.array.length)) {
				 return this.array[index];
			 }
			 return null;
		 },
		 add : function(key, value) {
			 var index = this.indexof(key);
			 if (index==-1) {
				 this.array.push({'key':key,'value':value});
				 this.__keys = null;
			 } else {
				 this.array[index].value = value;
			 }
			 return true;
		 },
		 get : function(key, def) {
			 var keys = this.keys();
			 if ((keys != null) && (keys.length>0)) {
				 index = $.inArray(key, this.keys());
				 if (index != -1) return this.array[index].value;
			 }
			 if ((def != 'undefined') && (def != null) && (def != '')) return def;
			 return (this.retString) ? '??'+key+'??' : null;
		 },
		 remove : function(key) {
			 index = this.indexof(key);
			 if (index != -1) {
				 this.array.splice(index,1);
				 this.__keys = null;
				 return true;
			 }
			 return false;
		 },
		 values : function() {
			 return $.map(this.array, function(a, index) { return a.value; });
		 },
		 keys : function() {
			 if (this.__keys != null) return this.__keys;
			 var out = $.map(this.array, function(a, index) { return a.key; });
			 this.__keys = out;
			 return this.__keys;
		 },
		 list : function() {
			 return this.array;
		 }
	 });

String.prototype.toEpoch = function() {
	var aDate = this.split('-');
	if (aDate.length < 3) {
		return new Date().getTime() / 1000;
	}
	var date = new Date(Date.UTC(aDate[2], aDate[1]-1, aDate[0], 0, 0, 0));
	var valueback = date.getTime() / 1000;
	return valueback;
};

String.prototype.guid = function() {
	var result, i, j;
	result = '';
	for(j=0; j<32; j++) {
		if( j == 8 || j == 12|| j == 16|| j == 20) result = result + '-';
		i = Math.floor(Math.random()*16).toString(16).toUpperCase();
		result = result + i;
	}
	return result;
};

Number.prototype.pad = function(padding) {
	var out = String(this);
	while (out.length < padding) {
		out = "0" + out;
	}
	return out;
}

Number.prototype.toFormatted = function(showComma) {
	if (showComma == null || showComma == 'undefined') {
		showComma = true;
	}
	var i = parseFloat(this);
	if (isNaN(i)) {
		i = 0.00;
	}
	var minus = (i < 0) ? '' : '';
	i = Math.abs(i);
	i = parseInt((i + .005) * 100);
	i = i / 100;
	var s = showComma ? Number(this).toLocaleString('en') : new String(i);
	if (s.indexOf('.') < 0) { s += '.00'; }
	if (s.indexOf('.') == (s.length - 2)) { s += '0'; }
	s = minus + s;
	return s;
};

Date.MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
Date.WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

// clone the current date object and return a different object with identical value
Date.prototype.clone = function () {
	return new Date(this.getTime());
};

// clear the time information from this date and return it
Date.prototype.clearTime = function () {
	this.setHours(0); this.setMinutes(0);
	this.setSeconds(0); this.setMilliseconds(0);
	return this;
};

Date.prototype.getDaysInMonth = function() {
	var m = [31,28,31,30,31,30,31,31,30,31,30,31];
	var today = new Date(this);
	if (today.getMonth() != 1) return m[today.getMonth()];
	if (today.getFullYear()%4 != 0) return m[1];
	if (today.getFullYear()%100 == 0 && today.getFullYear()%400 != 0) return m[1];
	return m[1] + 1;
};

guid = function() {
	return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
														  var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
														  return v.toString(16);
														  });
};

Date.prototype.getMonthStartsOn = function() {
	var today = new Date(this);
	today.setDate(1);
	return today.getDay();
};

// return the last day of this month
Date.prototype.lastDay = function () {
	var tempDate = this.clone();
	tempDate.setMonth(tempDate.getMonth()+1);
	tempDate.setDate(0);
	return tempDate.getDate();
};

Date.prototype.getWeek = function (dowOffset) {
	/*getWeek() was developed by Nick Baicoianu at MeanFreePath: http://www.meanfreepath.com */
	dowOffset = typeof(dowOffset) == 'int' ? dowOffset : 0; //default dowOffset to zero
	var newYear = new Date(this.getFullYear(),0,1);
	var day = newYear.getDay() - dowOffset; //the day of week the year begins on
	day = (day >= 0 ? day : day + 7);
	var daynum = Math.floor((this.getTime() - newYear.getTime() -
							 (this.getTimezoneOffset()-newYear.getTimezoneOffset())*60000)/86400000) + 1;
	var weeknum;
	//if the year starts before the middle of a week
	if(day < 4) {
		weeknum = Math.floor((daynum+day-1)/7) + 1;
		if(weeknum > 52) {
			nYear = new Date(this.getFullYear() + 1,0,1);
			nday = nYear.getDay() - dowOffset;
			nday = nday >= 0 ? nday : nday + 7;
			/*if the next year starts before the middle of
			 the week, it is week #1 of that year*/
			weeknum = nday < 4 ? 1 : 53;
		}
	}
	else {
		weeknum = Math.floor((daynum+day-1)/7);
	}
	return weeknum;
};

// return number of days since start of year
Date.prototype.getYearDay = function () {
	var today = new Date(this);
	today.setHours(0); today.setMinutes(0); today.setSeconds(0);
	var tempDate = new Date(today);
	// set start of year
	tempDate.setDate(1);
	tempDate.setMonth(0);
	return Math.round(
					  (today.getTime() - tempDate.getTime())
					  / 86400 / 1000) + 1; // Jan/1 is day 1
};

// add format() to Date
Date.prototype.format = function(formatString) {
	var out = new String();
	var token = "";
	for (var i = 0; i < formatString.length; i++) {
		if (formatString.charAt(i) == token.charAt(0)) {
			token = token.concat(formatString.charAt(i));
			continue;
		}
		out = out.concat(this.convertToken(token));
		token = formatString.charAt(i);
	}
	return out + this.convertToken(token);
};

// internal call to map tokens to the date data
Date.prototype.convertToken = function (str) {
	switch(str.charAt(0)) {
		case 'y': // set year
			if (str.length > 2)
				return this.getFullYear();
			return this.getFullYear().toString().substring(2);
		case 'd': // set date
			return Date.zeroPad(this.getDate(),str.length);
		case 'D': // set day in year
			return this.getYearDay();
		case 'a':
			return this.getHours() > 11 ? "PM" : "AM";
		case 'H': // set hours
			return Date.zeroPad(this.getHours(),str.length);
		case 'h':
			return Date.zeroPad(this.get12Hours(),str.length);
		case 'm': // set minutes
			return Date.zeroPad(this.getMinutes(),2);
		case 's': // set secondes
			return Date.zeroPad(this.getSeconds(),2);
		case 'S': // set milisecondes
			return Date.zeroPad(this.getMilliseconds(),str.length);
		case 'x': // set epoch time
			return this.getTime();
		case 'Z': // set time zone
			return (this.getTimezoneOffset() / 60) + ":" +
			Date.zeroPad(this.getTimezoneOffset() % 60,2);
		case 'M': // set month
			if (str.length > 3) return this.getFullMonthName();
			if (str.length > 2) return this.getShortMonthName();
			return Date.zeroPad(this.getMonth()+1,str.length);
		case 'E': // set dow
			if (str.length > 3) return this.getDOWName();
			if (str.length > 1) return this.getShortDOWName();
			return this.getDay();
		default:
			return str;
	}
};

// Retreive the month's name in english
Date.prototype.getFullMonthName = function() {
	return Date.MONTH_NAMES[this.getMonth()];
};

// Retreive the abberviated month name in english
Date.prototype.getShortMonthName = function() {
	return Date.MONTH_NAMES[this.getMonth()].substring(0,3);
};

// Retreive the week day name in english
Date.prototype.getDOWName = function () {
	return Date.WEEKDAY_NAMES[this.getDay()];
};

// Retreive the abberviated week day name in english
Date.prototype.getShortDOWName = function () {
	return Date.WEEKDAY_NAMES[this.getDay()].substring(0,3);
};

// Retreive the hour in a 12 hour clock (without the AM/PM specification)
Date.prototype.get12Hours = function () {
	return this.getHours() == 0 ? 12 :
	(this.getHours() > 12 ? this.getHours() - 12 : this.getHours());
};

Date.frommysql = function(timestamp) {
	//function parses mysql datetime string and returns javascript Date object
	//input has to be in this format: 2007-06-05 15:26:02
	var regex=/^([0-9]{2,4})-([0-1][0-9])-([0-3][0-9]) (?:([0-2][0-9]):([0-5][0-9]):([0-5][0-9]))?$/;
	var parts=timestamp.replace(regex,"$1 $2 $3 $4 $5 $6").split(' ');
	return new Date(parts[0],parts[1]-1,parts[2],parts[3],parts[4],parts[5]);
};

// helper function to add required zero characters to fixed length fields
Date.zeroPad = function(num, width) {
	num = num.toString();
	while (num.length < width)
		num = "0" + num;
	return num;
};

if (typeof console == 'undefined') {
	var console = {
	info: function() {},
	dir: function() {},
	group: function() {},
	groupEnd: function() {}
	};
};

jQuery.fn.sort = function() {
	return this.pushStack( [].sort.apply( this, arguments ), []);
};

String.prototype.bool = function() {
	return (/^true$/i).test(this);
};

String.prototype.endsWith = function(str) {return (this.match(str+"$")==str); };
String.prototype.startsWith = function(str) {return (this.match("^"+str)==str); };

String.prototype.format = function() {
	var s = this;
	if ((s == null) || (s == 'undefined')) return s;
	if (arguments==null) return s;
	var i = arguments.length;
	if (i>0) {
		while (i--) {
			s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
		}
	}
	return s;
};

if(!Array.indexOf){
	Array.prototype.indexOf = function(obj){
		for(var i=0; i<this.length; i++){
			if(this[i]==obj){
				return i;
			}
		}
		return -1;
	};
};

Array.prototype.findStr = function(searchStr) {
	var returnArray = false;
	if ((searchStr != null) && (searchStr != 'undefined')) {
		for (var i=0; i<this.length; i++) {
			if (typeof(searchStr) == 'function') {
				if (searchStr.test(this[i])) {
					if (!returnArray) { returnArray = []; }
					returnArray.push(i);
				}
			} else {
				if (this[i]===searchStr) {
					if (!returnArray) { returnArray = []; }
					returnArray.push(i);
				}
			}
		}
	}
	return returnArray;
};

String.prototype.formatArray = function(args) {
	var s = this;
	if ((s == null) || (s == 'undefined')) return s;
	if (args==null) return s;
	var i = args.length;
	if (i>0) {
		while (i--) {
			s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), args[i]);
		}
	}
	return s;
};

$.extend({
	URLEncode:function(c) {
		var o='';
		var x=0;
		c=c.toString();
		var r=/(^[a-zA-Z0-9_.]*)/;
		while(x<c.length){
			var m=r.exec(c.substr(x));
			if(m!=null&&m.length>1&&m[1]!=''){
				o+=m[1];
				x+=m[1].length;
			}else{
				if(c[x]==' ')o+='+';
				else{
					var d=c.charCodeAt(x);
					var h=d.toString(16);
					o+='%'+(h.length<2?'0':'')+h.toUpperCase();
				}
				x++;
			}
		}
		return o;
	},
	URLDecode: function(s) {
		var o=s;var binVal,t;
		var r=/(%[^%]{2})/;
		while((m=r.exec(o))!=null&&m.length>1&&m[1]!=''){
			b=parseInt(m[1].substr(1),16);
			t=String.fromCharCode(b);
			o=o.replace(m[1],t);
		}
		return o;
	}
});

App = {};

App.Core = {
	
	hasInit : false,
	
	__preinit : function() {
		if (this.hasInit) return;
		this.hasInit = true;
	},
	
};

App.Core.Security = {

	messageTop : -1,
	isLoggedIn : false,
	sessionId : null,
	refreshcount : 0,
	
	hasInit : false,
	
	__preinit : function() {
		if (this.hasInit) return;
		this.hasInit = true;
		$('*').bind('page-refresh page-changed', function(object, data) { App.Core.Security.refreshcount = 0; });
		App.Core.Security.checkLoginState();
	},
	
	checkloginStatus : function() {
		// trigger logout functionality at backend...
		var oData = {};
		var oRequest = {actions:[{action:'checkloginStatus', data:oData}]};
		App.Core.Application.appHandler(oEvent, oRequest);
	},
	
	recoverFailed : function() {
		this.checking = false;
	},
	
	checkLoginState : function() {
		if (this.checking) return;
		this.checking = true;
		var oData = {};
		$.ajax({
			   type: "get",
			   dataType: "json",
			   error: function(data) {
				   App.Core.Security.recoverFailed(data);
			   },
			   complete: function(response) {
				   var newCode = response.getResponseHeader("session_id");
				   if ((newCode != null) && (newCode != 'undefined') && (newCode != App.Core.Security.sessionId)) {
				   App.Core.Security.sessionId = newCode;
			   }
			   },
			   success: function(data) {
			   },
			   headers: {
				   "session_id":App.Core.Security.sessionId
			   },
			   url:'/__ping',
			   data:oData
		   });
	},
	
};

App.Core.Application = {
	
	hasInit : false,
	msgBox : $('#response .msg'),
	status : false,
	
	__preinit : function(){
		
		if (this.hasInit) return;
		this.hasInit = true;
		
		$('*').bind('do-submit', function(object, data){ App.Core.Application.__submit(data); });
		$('*').bind('do-ajaxsubmit', function(object, data){ App.Core.Application.__ajaxSubmit(data); });
		$('*').bind('do-formdata', function(object, data){ return App.Core.Application.__retrieveFormData(data); });
		
		$('*').bind('handle-app', function(object, data){ App.Core.Application.__appHandler(data); });
		$('*').bind('handle-status', function(object, data){ App.Core.Application.__handleStatus(data); });
		
		$(document).delegate('select', 'change', function(oEvent){ App.Core.Application.__handleEvent(oEvent, 'event'); });
		
		$(document).delegate('[data-event]:not(textarea):not(select):not([data-component="gmaps"])','click', function(oEvent){ App.Core.Application.__handleEvent(oEvent, 'event'); });
		$(document).delegate('[data-workflow]','click', function(oEvent){ App.Core.Application.__handleEvent(oEvent, 'workflow'); });
		
		$(document).delegate('textarea[data-maxlength], input[data-maxlength]', 'keyup', function(oEvent) {
							 
							 var maxlength = $(oEvent.currentTarget).attr("data-maxlength");
							 if ((maxlength == null) || (maxlength == 'undefined')) {
								 maxlength = -1;
							 } else {
								 maxlength = parseInt(maxlength)
							 }
							 
							 var content = $(oEvent.currentTarget).val();
							 if (maxlength == -1) {
							 } else {
								 var htmlout = "" + (maxlength - content.length);
								 $(" ~ span.remaining", $(oEvent.currentTarget)).html(htmlout);
							 }
							 
						 });
		
		$(document).delegate('textarea, input', 'keypress', function(oEvent) {
							 
							 var maxlength = $(oEvent.currentTarget).attr("data-maxlength");
							 if ((maxlength == null) || (maxlength == 'undefined')) {
								 maxlength = -1;
							 } else {
								 maxlength = parseInt(maxlength)
							 }
							 
							 var content = $(oEvent.currentTarget).val();
							 if (maxlength == -1) {
							 } else {
								 if (content.length < maxlength) {
								 } else {
									 oEvent.preventDefault();
									 return;
								 }
							 }
							 
							 if (oEvent.which == 13) {
							 
							 var allowEnter = $(oEvent.currentTarget).attr("data-allowreturn");
							 if ((allowEnter == null) || (allowEnter == 'undefined')) {
								 allowEnter = false;
							 } else {
								 allowEnter = parseInt(allowEnter) == 1;
							 }
							 
							 if (!allowEnter) oEvent.preventDefault();
							 var hasEvent = $(oEvent.target).attr("data-event");
							 
							 if ((hasEvent != null) && (hasEvent != 'undefined')) {
								 App.Core.Application.__handleEvent(oEvent, 'event');
							 } else {
								 $(oEvent.currentTarget).next('input').focus();
							 }
							 
						 }
							 
					 });
		
		//		$('[data-retrieve]').on('click', function(){ var el = $(this).data('retrieve'); $('*').triggerHandler('do-submit', { 'target':el, 'action':'myDetails' }); });
		
	},

	__handleEvent : function(oEvent, type, initiator) {
		
		var oElement = null;
		var attrs = null;
		
		if ((oEvent != null) && (oEvent != 'undefined')) {
			oElement = oEvent.currentTarget;
		}
		
		if ((oElement == null) || (oElement == 'undefined')) {
			attrs = oEvent;
			oElement = initiator;
		}
		
		var attr;
		
		if ((oElement == null) || (oElement == 'undefined')) return;
		
		if (type == 'event') {
			
			if (oElement.nodeName && oElement.nodeName.toLowerCase() == "select") {
				var index = oElement.selectedIndex;
				var option = oElement.options[index];
				var value = option.value;
				
				$(oElement).attr("data-selected", value);
				
				if ($(oElement).attr('data-event') != null) {
					attr = $(oElement).attr('data-event');
				} else {
					attr = $(option).attr('data-event');
				}
				
			} else {
				
				attr = $(oElement).data(type);
				
			}
			
		} else {
			
			attr = $(oElement).data(type);
			
		}
		
		for (_oArgs in eval('('+ attr +')')) {
			if(typeof _oArgs != 'function') var oArgs = eval('('+ attr +')');
			else console.info('No Functions allowed');
		}
		
		if (typeof oArgs != 'object') return;
		
		var functionFound = null;
		
		if ((oArgs.action != null || oArgs.action != undefined)) {
			
			// check core domain...
			var domain = App.Core[oArgs.action]
			
			if ((domain != null) && (domain != 'undefined')) {
				if (typeof domain[oArgs.event] == 'function') {
					functionFound = domain[oArgs.event];
				}
			}
			
			// check app domain...
			if ((functionFound == null) || (functionFound == 'undefiend')) {
				domain = Object.byString(App, oArgs.action);
				if ((domain != null) && (domain != 'undefined')) {
					if (typeof domain[oArgs.event] == 'function') {
						functionFound = domain[oArgs.event];
					}
				}
			}
			
		}
		
		if ((functionFound != null) && (functionFound != 'undefiend')) {
			functionFound(oElement, oArgs.args, attrs);
		} else {
			console.info('Function (Domain = ' + oArgs.action + ') / ' + oArgs.event + ' not found!');
		}
		
	},
	
	__retrieveFormData: function(data) {
		
		var uploads			= {};
		var oFormData		= {};
		var aInputs 		= $('#' + data.target + ' input, #' +  data.target + ' select, #' +  data.target + ' textarea');
		var oInput			= {};
		var sInputName		= '';
		var sInputValue		= '';
		var sDefaultValue	= '';
		var sInputTag		= '';
		
		for (var i = 0; i < aInputs.length; i++) {
			
			oInput			= aInputs[i];
			sInputTag		= oInput.nodeName;
			sInputType		= oInput.getAttribute('type');
			sInputName		= oInput.getAttribute('name');
			sInputValue		= oInput.value;
			sInputClass		= oInput.getAttribute('class');
			sDefaultValue	= oInput.getAttribute('data-default');
			
			if (sInputName != "ignore") {
				
				switch (sInputTag.toLowerCase()) {
						
					case "input": {
						
						if (sInputType == 'checkbox') {
							
							var isChecked = ((oInput.checked) ? 1 : 0);
							var value = oInput.getAttribute('value');
							
							if ((value == null) || (value == "undefined")) {
								sInputValue = isChecked;
							} else {
								sInputValue = isChecked ? value : null;
							}
							
							if (sInputValue != null) {
								
								var objType = jQuery.type(sInputValue);
								
								if (objType == "number") {
									oFormData[sInputName] = sInputValue;
								} else {
									if ((oFormData[sInputName] == null) || (oFormData[sInputName] == "undefined")) {
										oFormData[sInputName] = new Array();
									}
									oFormData[sInputName].push(sInputValue);
								}
								
							}
							
						} else if (sInputType == 'radio') {
							
							var aRadio = $('input[name='+sInputName+']:checked', '#'+data.target)
							
							for (var r=0; r < aRadio.length; r++) {
								if ((aRadio[r].getAttribute("data-value") != null) && (aRadio[r].getAttribute("data-value") != 'undefined')) {
									oFormData[sInputName] = aRadio[r].getAttribute("data-value");
								} else {
									oFormData[sInputName] = aRadio[r].getAttribute('value');
								}
							}
							
						} else if (sInputType == 'file') {
							
							sInputValue = $(oInput).attr("data-loadedcontent");
							
							if (sInputValue != null && sInputValue != 'undefined') {
								oFormData[sInputName] = sInputValue;
							}
							
							sInputValue = $(oInput).attr("data-filename");
							
							if (sInputValue != null && sInputValue != 'undefined') {
								oFormData[sInputName+"_filename"] = sInputValue;
							}
							
						} else if (typeof oFormData[sInputName] == 'string' && sInputType != 'radio') {
							
							var sOldValue = oFormData[sInputName];
							oFormData[sInputName] = [];
							oFormData[sInputName][oFormData[sInputName].length] = sOldValue;
							oFormData[sInputName][oFormData[sInputName].length]	= sInputValue;
							
						} else if (typeof oFormData[sInputName] == 'object') {
							
							oFormData[sInputName][oFormData[sInputName].length]	= sInputValue;
							
						} else {
							
							if (!$(oInput).hasClass('default')) {
								oFormData[sInputName] = sInputValue;
							}
							
						}
						
						break;
					}
						
					case "textarea": {
						
						if (oInput.tagName.toLowerCase() == 'textarea') {
							sInputValue = ((sInputClass == 'tinymce') ? tinyMCE.activeEditor.getContent() : oInput.value);
						}
						
						if (typeof oFormData[sInputName] == 'string' && sInputType != 'radio') {
							
							var sOldValue	= oFormData[sInputName];
							oFormData[sInputName] = [];
							oFormData[sInputName][oFormData[sInputName].length] = sOldValue;
							oFormData[sInputName][oFormData[sInputName].length]	= sInputValue;
							
						} else if (typeof oFormData[sInputName] == 'object') {
							
							oFormData[sInputName][oFormData[sInputName].length]	= sInputValue;
							
						} else {
							
							if (sDefaultValue != null && sDefaultValue != 'undefined') {
								if (sInputValue != sDefaultValue) {
									oFormData[sInputName] = sInputValue;
								} else {
									oFormData[sInputName] = "";
								}
							} else {
								oFormData[sInputName] = sInputValue;
							}
							
						}
						
						break;
					}
						
					case "select": {
						var selectedOption = $("option:selected", oInput);
						if (! selectedOption.is(":disabled")) {
							oFormData[sInputName] = sInputValue;
						}
						break;
					}
						
					default: {
						
						console.info("unknown tagtype - " + sInputTag.toLowerCase());
						break;
					}
						
				}
				
			}
			
		}
		
		return oFormData;
	},
	
	__appHandler : function(oRequest){
		
		var msgBox = $('#response .msg');
		
		var handleResponse = function(oData) {
			
			if (oData != null) {
				
				if (typeof oData.action != 'undefined') {
					
					var oArgs = (oData.args != null) ? oData.args : {};
					
					App[oData.action][oData.event](oArgs);
					
					domain = Object.byString(App, oData.action);
					if ((domain != null) && (domain != 'undefined')) {
						if (typeof domain[oData.event] == 'function') {
							functionFound = domain[oData.event];
							if ((functionFound != null) && (functionFound != 'undefined')) {
								functionFound(null, oArgs.args);
							}
						}
					}
					
				} else {
					
					$('*').triggerHandler('handle-status', oData);
					
				}
				
			} else {
				console.info('No data received');
			}
		};
		
		var oData = $.toJSON(oRequest);
		
		$.ajax({
			   async: false,
			   xhr: function() {
			   var xhr = new window.XMLHttpRequest();
			   
			   // Upload progress
			   xhr.upload.addEventListener("progress", function(evt){
										   if (evt.lengthComputable) {
										   var percentComplete = evt.loaded / evt.total;
										   //Do something with upload progress
										   console.info("progress = " + percentComplete);
										   }
										   }, false);
			   
			   // Download progress
			   xhr.addEventListener("progress", function(evt){
									if (evt.lengthComputable) {
									var percentComplete = evt.loaded / evt.total;
									// Do something with download progress
									console.info("progress = " + percentComplete)
									}
									}, false);
			   
			   return xhr;
			   },
			   type: "gateway",
			   cache: false,
			   processData: false,
			   contentType: "application/json",
			   headers: {
				   "session_id":App.Core.Security.sessionId
			   },
			   url: "",
			   data: oData,
			   success: handleResponse
		   });
		
	},
	
	__handleStatus : function(oData){
		
		switch (oData.mode){
				
			case 'messagebox': { // message box
				alert(oData.message);
				break;
			}
				
			case 'window-refresh': {
				var x = location.hash;
				if ((oData.delay != null) && (oData.delay != 'undefined')) {
					setTimeout(function() {
							   location.reload(true);
						   }, oData.delay);
				} else {
					location.reload(true);
				}
				break;
			}
				
			default:
				break;
				
		}
		
	},
	
	__createMsg : function(status, oData){
		
		var msgBox = this.msgBox;
		var status = (status) ? 'true' : 'false';
		
		var msg = '<div class="msg '+ status +'">'+ oData.message +'</div>';
		
		if($(msgBox).is(':visible')){
			$('#response').prepend(msg).slideUp('50', function(){ $('#response .msg').fadeIn('50'); });
		} else {
			$('#response').append(msg).slideDown('50', function(){ $('#response .msg').fadeIn('50'); });
		}
		
	},
	
	__clearMsg : function(){
		var parent = $('#response');
		$(parent).slideUp('50');
		$('.msg', parent).fadeOut('50', function(){ $('.msg', parent).remove(); });
		
	},
	
	__submit: function(data) {
		
		if(data.target != null) var oFormData = this.__retrieveFormData(data);
		else console.info('Target is not set');
		
		if ((data['action'] != null) || (data['action'] != 'undefined')) var oRequest = {actions:[{action:data.action,data:oFormData}]};
		else console.info('No action available');
		
		this.__appHandler(oRequest);
		
	},
	
	__ajaxSubmit : function(data){
		
		var oForm = $('#'+ data.form);
		var config = {
			target : App.Core.Application.msgBox,
			dataType : 	'json',
			success : function(oData){
				$('*').triggerHandler('handle-status', oData);
			}
		};
		
		$(oForm).ajaxSubmit(config);
	}
	
};


$(document).ready(function() {
				  				  
				  App.Core.__preinit();
				  App.Core.Security.__preinit();
				  App.Core.Application.__preinit();
				  
			  });
