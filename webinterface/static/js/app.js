


var app = angular.module("SecPi", ['ngAnimate']);

app.service('FlashService', function($log, $timeout){
	var self = this;
	
	self.TYPE_INFO = 'info';
	self.TYPE_WARN = 'warn';
	self.TYPE_ERR = 'error';
	
	self.flash_messages = [];
	
	self.flash = function(message,type){
		msg = {message: message, type: type}
		self.flash_messages.push(msg);
		
		$timeout(self.removeFlash, 5000)
	};
	
	self.removeFlash = function(){
		if(self.flash_messages.length > 0){
			self.flash_messages.splice(0,1); // remove first element from array
		}
	};
	
	self.handle_error = function(response){
		self.flash(('Error with status ' +response.status +' while retrieving data!'), self.TYPE_ERR);
	}
});


app.service('HTTPService', ['$http', 'FlashService', function($http, FlashService){
	var self = this;
	
	self.post = function(path, data, success_func){
		$http.post(path, data).then(
			function (response) {
				// success
				if(response.data['status'] == 'success'){
					success_func(response.data['data'], response.data['message']);
				}
				else{
					FlashService.flash(response.data['message'], FlashService.TYPE_ERR);
				}
			},
			FlashService.handle_error
		);
	}
	
}]);

app.controller('FlashController', ['FlashService', function(FlashService){
	var self = this;
	
	self.messages = FlashService.flash_messages;
	
	self.flash = function(message,type){
		FlashService.flash(message,type);
	}
}])

app.controller('DataController', ['$http', '$log', '$scope', '$timeout', '$attrs', 'FlashService', 'HTTPService', function($http, $log, $scope, $timeout, $attrs, FlashService, HTTPService){
	var self = this;
	
	if (!$attrs.baseclass) throw new Error("No class defined!");
	if (!$attrs.basetitle) throw new Error("No title defined!");
	
	self.baseclass = "/"+$attrs.baseclass;
	self.basetitle = $attrs.basetitle;
	
	if ($attrs.queryfilter){
		self.query_filter = $attrs.queryfilter;
	}
	
	
	self.data = [];
	self.fields = {};
	self.form_fields = {}
	
	self.edit_data = null;
	self.edit_id = -1;
	self.orig_data = null;
	
	
	self.edit_active = true;
	HTTPService.post('/setups/list', {"filter":"active_state==1"},
		function(data, msg){
			// FlashService.flash("got data: "+ angular.toJson(data), FlashService.TYPE_INFO);
			if(data.length > 0){ // we got an active setup, disable edit
				self.edit_active = false;
			}
		}
	);
	
	
	self.fetchFields = function(){
		HTTPService.post(self.baseclass+'/fieldList', {},
			function(data, msg){
				self.fields = data;
			}
		);
	}
	
	self.getFields = function(filter){
		return self.filter_fields(filter);
	}
	
	self.filter_fields = function(filter) {
		var filtered_fields = {};
		
		for (var key in self.fields) {
			if (self.fields.hasOwnProperty(key)) {
				if($.inArray(filter, self.fields[key]['visible']) >= 0){
					filtered_fields[key] = self.fields[key];
				}
			}
		}
		
		return filtered_fields;
	}
	
	
	self.getList = function(){
		$log.log('fetching list')
		var list_data = {}
		if(self.query_filter){
			list_data = {"filter": self.query_filter}
		}
		
		HTTPService.post(self.baseclass+'/list', list_data,
			function(data, msg){
				self.data = data;
			}
		);
	};
	
	self.showEdit = function(id){
		self.form_fields = self.getFields('update')
		self.dialog.dialog('option', 'title', 'Edit '+self.basetitle);
		self.edit_data = self.data[id];
		self.edit_id = id;
		self.orig_data = jQuery.extend(true, {}, self.data[id])
		self.dialog.dialog("open");
	};
	
	self.saveEdit = function(){ 
		$log.log("saving stuff")
		if(self.edit_id == -1){ // if edit id is -1 we are adding a new one
			HTTPService.post(self.baseclass+'/add', self.edit_data,
				function(data, msg){
					FlashService.flash(msg, FlashService.TYPE_INFO)
					
					// self.data.push(self.edit_data); // won't get id of saved element
					self.getList();
					
					self.orig_data = null;
					self.edit_data = null;
					self.edit_id = -1;
					
					self.dialog.dialog( "close" );
				}
			);
		}
		else{
			HTTPService.post(self.baseclass+'/update', self.edit_data,
				function(data, msg){
					FlashService.flash(msg, FlashService.TYPE_INFO)
					self.orig_data = null;
					self.edit_data = null;
					self.edit_id = -1;
					self.dialog.dialog( "close" );
				}
			);
		}
	};
	
	self.cancelEdit = function(){
		$log.log("cancel "+self.edit_id);
		self.data[self.edit_id] = self.orig_data;
		self.orig_data = null;
		self.edit_data = null;
		self.edit_id = -1;
		$scope.$apply();
		self.dialog.dialog( "close" );
	};
	
	self.showNew = function(){
		self.form_fields = self.getFields('add')
		self.dialog.dialog('option', 'title', 'Add '+self.basetitle);
		self.edit_data = {};
		self.edit_id = -1;
		self.dialog.dialog("open");
	};
	
	self.delete = function(delId){
		if(confirm("Do you really want to delete the Object with id "+ delId +"?")){
			HTTPService.post(self.baseclass+'/delete', {id: self.data[delId]["id"]},
				function(data, msg){
					FlashService.flash(msg, FlashService.TYPE_INFO)
					self.data.splice(delId, 1);
				}
			);
		}
	};
	
	
	
	$timeout(function(){
		self.dialog = $( "#edit-form-div" ).dialog({
			autoOpen: false,
			height: 300,
			width: 350,
			modal: true,
			buttons: {
				"Save": function(){
					self.saveEdit();
				},
				Cancel: function() {
					self.cancelEdit();
				}
			}
		});
		$(".ui-dialog-titlebar-close").remove();
	}, 100)
	
	
	
	self.fetchFields();
	self.getList();
}]);




app.controller('LogController', ['$http', '$log', '$interval', 'FlashService', 'HTTPService', function($http, $log, $interval, FlashService, HTTPService){
	var self = this;
	
	self.log_entries = [];
	
	self.fetchLog = function(){
		HTTPService.post('/logs/list', {"filter":"ack==0"},
			function(data, msg){
				if(angular.toJson(data) != angular.toJson(self.log_entries)){
					self.log_entries = data;
				}
			}
		);
	};
	
	self.ack = function(log_id){
		HTTPService.post('/logs/ack', {"id":self.log_entries[log_id].id},
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.log_entries.splice(log_id, 1);
			}
		);
	}
	
	self.refresh = function(){
		self.fetchLog();
	}
	
	self.fetchLog();
	// refresh list every 5 seconds 
	self.refresh_inter = $interval(self.refresh, 5000);
}]);



app.controller('ActivateController', ['$http', '$log', '$interval', 'FlashService', 'HTTPService', function($http, $log, $interval, FlashService, HTTPService){
	var self = this;
	
	self.inactive_setups = [];
	self.active_setups = [];
	
	self.fetch_active = function(){
		HTTPService.post('/setups/list', {"filter":"active_state==1"}, function(data, msg){self.active_setups = data})
	}
	
	self.fetch_inactive = function(){
		HTTPService.post('/setups/list', {"filter":"active_state==0"}, function(data, msg){self.inactive_setups = data})
	}
	
	self.activate = function(){
		if(self.activate_setup){
			HTTPService.post('/activate', {"id": self.activate_setup.id}, 
				function(data,msg){
					FlashService.flash(msg, FlashService.TYPE_INFO);
					self.fetch_active();
					self.fetch_inactive();
				}
			);
		}
	}
	
	self.deactivate = function(){
		if(self.deactivate_setup){
			HTTPService.post('/deactivate', {"id": self.deactivate_setup.id}, 
				function(data,msg){
					FlashService.flash(msg, FlashService.TYPE_INFO);
					self.fetch_active();
					self.fetch_inactive();
				}
			);
		}	
	}
	
	
	self.fetch_active();
	self.fetch_inactive();
}]);


app.controller('SetupsZonesController', ['$log', '$timeout', 'FlashService', 'HTTPService', function($log, $timeout, FlashService, HTTPService){
	var self = this;
	
	self.setups_zones = [];
	self.setups = [];
	self.zones = [];
	
	
	self.fetchData = function(){
		HTTPService.post('/setupszones/list', {},
			function(data,msg){
				self.setups_zones = data;		
			}
		);
		
		HTTPService.post('/setups/list', {},
			function(data,msg){
				self.setups = data;		
			}
		);
		
		HTTPService.post('/zones/list', {},
			function(data,msg){
				self.zones = data;		
			}
		);
	}
	
	self.showAdd = function(){
		self.dialog.dialog("open");
	}
	
	self.save = function(){
		HTTPService.post('/setupszones/add', {"setup_id": self.setup.id, "zone_id": self.zone.id},
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.fetchData();
				self.dialog.dialog( "close" );
			}
		);
		
		
	}
	
	self.cancel = function(){
		self.dialog.dialog( "close" );
		
	}
	
	self.delete = function(setup_id, zone_id){
		if(confirm("Do you really want to delete this association?")){
			HTTPService.post('/setupszones/delete', {"setup_id": setup_id, "zone_id": zone_id},
				function(data, msg){
					FlashService.flash(msg, FlashService.TYPE_INFO);
					self.fetchData();
				}
			);
		}
	}
	
	
	$timeout(function(){
		self.dialog = $( "#sz-form" ).dialog({
			autoOpen: false,
			height: 300,
			width: 350,
			modal: true,
			buttons: {
				"Save": function(){
					self.save();
				},
				Cancel: function() {
					self.cancel();
				}
			}
		});
		$(".ui-dialog-titlebar-close").remove();
	}, 100)
	
	self.fetchData();
}]);






