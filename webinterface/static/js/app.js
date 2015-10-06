


var app = angular.module("SecPi", ['ngAnimate']);

app.service('FlashService', function($log, $timeout){
	var self = this;
	
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
		self.flash('Error with status %s while retrieving data: %s' %(response.status, response.data), 'error');
	}
});

app.controller('FlashController', ['FlashService', function(FlashService){
	var self = this;
	
	self.messages = FlashService.flash_messages;
	
	self.flash = function(message,type){
		FlashService.flash(message,type);
	}
}])

app.controller('DataController', ['$http', '$log', '$scope', '$timeout', '$attrs', 'FlashService', function($http, $log, $scope, $timeout, $attrs, FlashService){
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
	
	
	
	self.fetchFields = function(){
		$http.post(self.baseclass+'/fieldList', {}).then(
			function (response) {
				// success
				if(response.data['status'] == 'success'){
					self.fields = response.data['data'];
				}
				else{
					FlashService.flash(response.data['message'], 'error');
				}
			},
			FlashService.handle_error
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
		$http.post(self.baseclass+'/list', list_data).then(
			function (response) {
				// success
				if(response.data['status'] == 'success'){
					self.data = response.data['data'];
				}
				else{
					FlashService.flash(response.data['message'], 'error');
				}
			},
			FlashService.handle_error
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
			
			$http.post(self.baseclass+'/add', self.edit_data).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						FlashService.flash(response.data['message'], 'info')
						
						
						// self.data.push(self.edit_data); // won't get id of saved element
						self.getList();
						
						self.orig_data = null;
						self.edit_data = null;
						self.edit_id = -1;
						
						
						self.dialog.dialog( "close" );
					}
					else{
						FlashService.flash(response.data['message'], 'error');
					}
				},
				FlashService.handle_error
			);
		}
		else{
			$http.post(self.baseclass+'/update', self.edit_data).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						FlashService.flash(response.data['message'], 'info')
						self.orig_data = null;
						self.edit_data = null;
						self.edit_id = -1;
						self.dialog.dialog( "close" );
					}
					else{
						FlashService.flash(response.data['message'], 'error');
					}
				},
				FlashService.handle_error
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
			$http.post(self.baseclass+'/delete', {id: self.data[delId]["id"]}).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						FlashService.flash(response.data['message'], 'info')
						self.data.splice(delId, 1);
					}
					else{
						FlashService.flash(response.data['message'], 'error');
					}
				},
				FlashService.handle_error
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




app.controller('LogController', ['$http', '$log', '$scope', '$timeout', '$attrs', 'FlashService', function($http, $log, $scope, $timeout, $attrs, FlashService){
	var self = this;
	
	self.log_entries = [];
	
	self.fetchLog = function(){
		$log.log('fetching log')
		$http.post('/logs/list', {"filter":"ack==0"}).then(
			function (response) {
				// success
				if(response.data['status'] == 'success'){
					self.log_entries = response.data['data'];
				}
				else{
					FlashService.flash(response.data['message'], 'error');
				}
			},
			FlashService.handle_error
		);
	};
	
	self.ack = function(log_id){
		
		$http.post('/logs/ack', {"id":self.log_entries[log_id].id}).then(
			function (response) {
				// success
				if(response.data['status'] == 'success'){
					FlashService.flash(response.data['message'], 'info');
					self.log_entries.splice(log_id, 1);
				}
				else{
					FlashService.flash(response.data['message'], 'error');
				}
			},
			FlashService.handle_error
		);
	}
	
	self.fetchLog();
}]);

app.controller('ActivateController', function($http, $log, $scope, $timeout, $attrs){
	var self = this;
		
});


