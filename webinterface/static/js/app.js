


var app = angular.module("SecPi", ['ngAnimate']);

app.service('FlashService', function($log, $timeout){
	var self = this;
	
	self.TYPE_INFO = 'info';
	self.TYPE_WARN = 'warn';
	self.TYPE_ERR = 'error';
	
	self.flash_messages = {};
	
	self.id = 0;
	
	self.flash = function(message,type,time){
		var id = ++self.id;
		if(!time){
			time = 5000;
		}
		msg = {message: message, type: type, id:id}
		self.flash_messages[id] = msg;
		
		$timeout(self.removeFlash, time, true, id)
	};
	
	self.removeFlash = function(id){
		if(self.flash_messages.hasOwnProperty(id)){
			delete self.flash_messages[id];
		}
	};
	
	self.handle_error = function(response){
		self.flash(('Error with status ' +response.status +' while retrieving data!'), self.TYPE_ERR);
	}
});


app.service('HTTPService', ['$http', 'FlashService', function($http, FlashService){
	var self = this;
	
	self.post = function(path, data, success_func, err_func){
		$http.post(path, data).then(
			function (response) {
				// success
				if(response.data['status'] == 'success'){
					success_func(response.data['data'], response.data['message']);
				}
				else{
					FlashService.flash(response.data['message'], FlashService.TYPE_ERR);
					err_func();
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
	
	self.loading = true;
	
	
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
		self.loading = true;
		$log.log('fetching list')
		var list_data = {}
		if(self.query_filter){
			list_data = {"filter": self.query_filter}
		}
		
		HTTPService.post(self.baseclass+'/list', list_data,
			function(data, msg){
				self.data = data;
				self.loading = false;
			},
			function(){
				self.loading = false;
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
		self.loading = true;
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
					self.loading = false;
				},
				function(){
					self.loading = false;
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
					self.loading = false;
				},
				function(){
					self.loading = false;
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
					self.loading = false;
				},
				function(){
					self.loading = false;
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
	
	self.loading = false;
}]);


app.controller('AckController', ['$http', '$log', '$interval', '$attrs', 'FlashService', 'HTTPService', function($http, $log, $interval, $attrs, FlashService, HTTPService){
	var self = this;
	
	if (!$attrs.ackclass) throw new Error("No class defined!");
	
	self.ackclass = $attrs.ackclass;
	
	
	self.entries = [];
	
	self.fetchData = function(){
		HTTPService.post('/' +self.ackclass +'s/list', {"filter":"ack==0"},
			function(data, msg){
				if(angular.toJson(data) != angular.toJson(self.entries)){
					self.entries = data;
				}
			}
		);
	};
	
	self.ack = function(ent_id){
		HTTPService.post('/' +self.ackclass +'s/ack', {"id":self.entries[ent_id].id},
			function(data, msg){
				FlashService.flash(msg, FlashService.TYPE_INFO);
				self.entries.splice(ent_id, 1);
			}
		);
	}
	
	self.ackAll = function(){
		for (i=0; i<self.entries.length;i++) {
			self.ack(i)
		}
		
		FlashService.flash("Acknowledged all messages!", FlashService.TYPE_INFO);
		self.fetchData();
	}
	
	self.refresh = function(){
		self.fetchData();
	}
	
	self.toggleRefresh = function(){
		if(self.refresh_inter){
			self.stopRefresh();
		}
		else{
			self.startRefresh();
		}
	}
	
	self.startRefresh = function(){
		// refresh list every 5 seconds
		if(!self.refresh_inter){
			self.refresh_inter = $interval(self.refresh, 5000);
			FlashService.flash('Started refresh of messages!', FlashService.TYPE_INFO, 2000);
			$('#refresh_toggle_'+self.ackclass).prop('value', "stop refresh");
		}
	}
	
	self.stopRefresh = function(){
		if(self.refresh_inter){
			$interval.cancel(self.refresh_inter);
			self.refresh_inter = null;
			FlashService.flash('Stopped refresh of messages!', FlashService.TYPE_INFO, 2000);
			$('#refresh_toggle_'+self.ackclass).prop('value', "start refresh");
		}
	}
	
	self.fetchData();
	
	self.startRefresh()
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


app.controller('ConfigController', ['$log', 'FlashService', 'HTTPService', function($log, FlashService, HTTPService){
	var self = this;
	
	
}]);


app.controller('RelationshipController', ['$log', '$timeout', '$attrs', 'FlashService', 'HTTPService', function($log, $timeout, $attrs, FlashService, HTTPService){
	var self = this;
	
	if (!$attrs.leftclass) throw new Error("No left class defined!");
	if (!$attrs.rightclass) throw new Error("No right class defined!");
	
	self.leftclass = $attrs.leftclass;
	self.rightclass = $attrs.rightclass;
	
	self.leftname = $attrs.leftname?$attrs.leftname:$attrs.leftclass;
	self.rightname = $attrs.rightname?$attrs.rightname:$attrs.rightclass;
	
	
	self.lefts_rights = [];
	self.lefts = [];
	self.rights = [];
	
	
	self.edit_active = true;
	HTTPService.post('/setups/list', {"filter":"active_state==1"},
		function(data, msg){
			// FlashService.flash("got data: "+ angular.toJson(data), FlashService.TYPE_INFO);
			if(data.length > 0){ // we got an active setup, disable edit
				self.edit_active = false;
			}
		}
	);
	
	self.fetchData = function(){
		HTTPService.post('/' +self.leftclass +'s' +self.rightclass +'s/list', {},
			function(data,msg){
				self.lefts_rights = data;		
			}
		);
		
		HTTPService.post('/' +self.leftclass +'s/list', {},
			function(data,msg){
				self.lefts = data;
			}
		);
		
		HTTPService.post('/' +self.rightclass +'s/list', {},
			function(data,msg){
				self.rights = data;
			}
		);
	}
	
	self.showAdd = function(){
		self.dialog.dialog("open");
	}
	
	self.save = function(){
		var dat = {};
		dat[self.leftclass+"_id"] = self.left.id;
		dat[self.rightclass+"_id"] = self.right.id;
		HTTPService.post('/' +self.leftclass +'s' +self.rightclass +'s/add', dat,
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
	
	self.delete = function(left_id, right_id){
		if(confirm("Do you really want to delete this association?")){
			var dat = {};
			dat[self.leftclass+"_id"] = left_id;
			dat[self.rightclass+"_id"] = right_id;
			HTTPService.post('/' +self.leftclass +'s' +self.rightclass +'s/delete', dat,
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
			height: 200,
			width: 200,
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




