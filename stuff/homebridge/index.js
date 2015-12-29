var request = require("request");
var Service, Characteristic;

module.exports = function(homebridge) {
  Service = homebridge.hap.Service;
  Characteristic = homebridge.hap.Characteristic;
  
  homebridge.registerAccessory("homebridge-secpi", "SecPi", SecPiAccessory);
}

function SecPiAccessory(log, config) {
	this.log = log;
	this.name = config["name"];

}

SecPiAccessory.prototype.getState = function(callback) {
	
}

SecPiAccessory.prototype.setState = function(callback) {
	
}

SecPiAccessory.prototype.getServices = function(callback) {
	
}
