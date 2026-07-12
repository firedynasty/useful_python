/* CCPA Implementation - USP API */
var SekindoClientDetections_CCPA = function (isDebug, defConsent, onConsentAvail) {
	this.CONSENT_REJECTED = 0;
	this.CONSENT_APPROVED = 1;
	this.CONSENT_NOT_APPLY = 2;

	this.VERSION = 1;

	this.consentRawData = null;
	this.debug = isDebug;
	this.defConsent = defConsent;

	if (onConsentAvail && typeof onConsentAvail == 'function')
		this.onConsentAvail = onConsentAvail;
	else
		this.onConsentAvail = null;

	this.uspCallsList = {};

	if (typeof window.Sekindo == 'undefined')
		window.Sekindo = {};
	if (typeof window.Sekindo.clientConsentEncoded == 'undefined')
		window.Sekindo.clientConsentEncoded = null;

	this.getState = function()
	{
		return this.consentState;
	};

	this.getConsent = function()
	{
		return this.consentRawData ? this.consentRawData : this.defConsent;
	};

	this._postMessage = function (cb, command)
	{
		try
		{
			window.addEventListener('message', cb);

			var tempTs = new Date().getTime();
			var callId = "PrimisCcpaCall_"+command+"_"+Math.random().toString()+"_"+tempTs.toString();
			this.uspCallsList[callId] = command;
			var message = {
				__uspapiCall: {
					callId: callId,
					command: command,
					parameter: null,
					version: this.VERSION
				}
			};
			if (this.debug)
				console.log("SEKDBG/CCPA: Sending message '"+command+"' to USP");
			window.top.postMessage(message, '*');
			return true;
		}
		catch (e)
		{
			if (this.debug)
			{
				console.log("SEKDBG/CCPA: Failed to send message '"+command+"' to USP");
				console.log(e);
			}
			return false;
		};
	};

	this._call = function (command)
	{
		var ref = this;

		try
		{
			window.top.__uspapi(command, this.VERSION, this.uspCallbacksList[command]);
			if (ref.debug)
				console.log("SEKDBG/CCPA: Using DIRECT/"+command);
		}
		catch (e)
		{
			try
			{
				__uspapi(command, this.VERSION, this.uspCallbacksList[command]);
				if (this.debug)
					console.log("SEKDBG/CCPA: Using SAFE_FRAME/"+command);
			}
			catch (eSf)
			{
				if (this.debug)
					console.log("SEKDBG/CCPA2: Using MESSAGING/"+command);
				this._postMessage(function (evt) {
					if (evt && evt.data && evt.data.__uspapiReturn && evt.data.__uspapiReturn.returnValue && evt.data.__uspapiReturn.callId)
					{
						if (ref.debug)
							console.log("SEKDBG/CCPA: Received message '"+evt.data.__uspapiReturn.callId+"' from channel");
						if (ref.uspCallsList.hasOwnProperty(evt.data.__uspapiReturn.callId))
						{
							if (typeof ref.uspCallsList[evt.data.__uspapiReturn.callId] === 'string')
							{
								var cmd = ref.uspCallsList[evt.data.__uspapiReturn.callId];
								if (ref.uspCallbacksList.hasOwnProperty(cmd) && typeof ref.uspCallbacksList[cmd] === 'function')
									ref.uspCallbacksList[cmd](evt.data.__uspapiReturn.returnValue);
							}
							delete ref.uspCallsList[evt.data.__uspapiReturn.callId];
						}
					}
					else if (ref.debug && evt && evt.data && evt.data.__uspapiReturn)
					{
						console.log("SEKDBG/CCPA: Received corrupted message from channel");
						console.log(evt);
					}
				}, command);
			}
		}
	};

	this._verify = function (uspData)
	{
		if (typeof uspData !== 'object')
		{
			if (this.debug)
			{
				console.log("SEKDBG/CCPA: Bad consent data is provided as not object");
				console.log(rawConsent);
			}
			this.consentState = this.CONSENT_REJECTED;
			return false;
		}
		rawConsent = uspData.uspString || null;

		if (typeof rawConsent !== 'string' || rawConsent.length != 4)
		{
			if (this.debug)
			{
				console.log("SEKDBG/CCPA: Bad consent data is provided");
				console.log(rawConsent);
			}
			this.consentState = this.CONSENT_REJECTED;
			return false;
		}

		if (rawConsent === this.VERSION+'---')
		{
			if (this.debug)
				console.log("SEKDBG/CCPA: CCPA does not apply for this client");
			this.consentState = this.CONSENT_NOT_APPLY;
			return true;
		}

		if (this.debug)
		{
			console.log("SEKDBG/CCPA: Consent returned by SDK:");
			console.log(rawConsent);
		}

		if (rawConsent[0] != this.VERSION) /* Check protocol version */
		{
			if (this.debug)
			{
				console.log("SEKDBG/CCPA: Bad consent version is provided");
				console.log(rawConsent);
			}
			this.consentState = this.CONSENT_REJECTED;
			this.consentRawData = rawConsent;
			return false;
		}

		if (rawConsent[2] == 'Y') /* Client Opt-Out flag */
		{
			if (this.debug)
			{
				console.log("SEKDBG/CCPA: Consent opted-out of data sale");
				console.log(rawConsent);
			}
			this.consentState = this.CONSENT_REJECTED;
			this.consentRawData = rawConsent;
			return false;
		}

		this.consentState = this.CONSENT_APPROVED;
		this.consentRawData = rawConsent;

		if (this.debug)
			console.log("SEKDBG/CCPA: Approval received");

		return true;
	};

	var ref = this;

	this.uspCallbacksList = {
		getUSPData: function (result, success) {
				if (!success)
					return;

				ref._verify(result);

				/* On success/non-required, call the availability callback */
				if (ref.onConsentAvail && (ref.consentState == ref.CONSENT_APPROVED || ref.consentState == ref.CONSENT_REJECTED))
					ref.onConsentAvail(ref.getConsent(), ref.consentState == ref.CONSENT_REJECTED);
		}
	};

	/* Get USP Information */
	this._call('getUSPData', null);
};