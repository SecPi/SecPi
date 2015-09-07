


var app = angular.module("SecPi", []);

app.controller('DataController', function($http, $log, $scope, $timeout, $attrs){
		var self = this;
		
		if (!$attrs.baseclass) throw new Error("No class defined!");
		if (!$attrs.basetitle) throw new Error("No title defined!");
		
		self.baseclass = "/"+$attrs.baseclass;
		self.basetitle = $attrs.basetitle;
		
		
		self.flash_message = null;
		self.flash_type = 'info';
		
		self.data = [];
		self.fields = {};
		
		self.edit_data = null;
		self.edit_id = -1;
		self.orig_data = null;
		
		self.flash = function(message,type){
			self.flash_message = message;
			self.flash_type = type;
			
			$timeout(function(){self.flash_message = null}, 5000)
		}
		
		
		self.fetchFields = function(){
			$http.post(self.baseclass+'/fieldList', {}).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.fields = response.data['data'];
					}
					else{
						self.flash(response.data['message'], 'error');
					}
				},
				function (response) {
					// error
					self.flash('Error retrieving data!', 'error');
				}
			)
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
			$http.get(self.baseclass+'/list').then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.data = response.data['data'];
					}
					else{
						self.flash(response.data['message'], 'error');
					}
				},
				function (response) {
					// error
					self.flash('Error retrieving data!', 'error');
				})	
		};
		
		self.showEdit = function(id){
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
							self.flash(response.data['message'], 'info')
							
							
							// self.data.push(self.edit_data); // won't get id of saved element
							self.getList();
							
							self.orig_data = null;
							self.edit_data = null;
							self.edit_id = -1;
							
							
							self.dialog.dialog( "close" );
						}
						else{
							sself.flash(response.data['message'], 'error');
						}
					},
					function (response) {
						// error
						self.flash('Error saving data!', 'error');
					}
				);
			}
			else{
				$http.post(self.baseclass+'/update', self.edit_data).then(
					function (response) {
						// success
						if(response.data['status'] == 'success'){
							self.flash(response.data['message'], 'info')
							self.orig_data = null;
							self.edit_data = null;
							self.edit_id = -1;
							self.dialog.dialog( "close" );
						}
						else{
							sself.flash(response.data['message'], 'error');
						}
					},
					function (response) {
						// error
						self.flash('Error saving data!', 'error');
					}
				)
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
			self.dialog.dialog('option', 'title', 'Add '+self.basetitle);
			self.edit_data = {};
			self.edit_id = -1;
			self.dialog.dialog("open");
		};
		
		self.delete = function(delId){
			// TODO: confirm
			$http.post(self.baseclass+'/delete', {id: self.data[delId]["id"]}).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.flash(response.data['message'], 'info')
						self.data.splice(delId, 1);
					}
					else{
						sself.flash(response.data['message'], 'error');
					}
				},
				function (response) {
					// error
					self.flash('Error saving data!', 'error');
				}
			)
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
})



