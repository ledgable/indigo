
App.Example = {
	
	hasInit : false,
	
	__preinit : function() {
		if (this.hasInit) return;
		this.hasInit = true;
	}
	
};

App.Example.Extended = {
	
	testjscall : function(oEvent, oArgs) {
		
		var oData = $('*').triggerHandler('do-formdata', {'target':'deploy__info'});
		oData.uid = oArgs.uid;
		
		var oRequest= {actions:[{action:'testjscallserverside', data:oData}]};
		$('*').triggerHandler('handle-app', oRequest);
		
	}
	
};

$(document).ready(function() {
				  
				  App.Example.__preinit();
				  
				  });

