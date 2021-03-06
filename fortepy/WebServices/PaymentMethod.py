from .WebService import WebService
import pickle
import six
import base64

class PaymentMethod(WebService):
	REQUIRE_COMPLIANCE = False
	def __init__(self, record=None, **kwargs):
		super(PaymentMethod, self).__init__()
		self._client = None
		r = record if record else self.default_record
		if not PaymentMethod.REQUIRE_COMPLIANCE:
			try:
				enc = base64.b64decode(r.Note)
				self._data = pickle.loads(enc)
			except Exception as e:
				self._data = {'note':r.Note}
		self._record = r
		for key, value in kwargs.items():
			setattr(self, key, value)

	@property
	def default_record(self):
		record = WebService.CLIENT.factory.create('PaymentMethod')
		record.AcctHolderName = ""
		record.CcCardNumber = ""
		record.CcExpirationDate = ""
		record.CcCardType = None
		record.CcProcurementCard = False
		record.EcAccountNumber = ""
		record.EcAccountTRN = ""
		record.EcAccountType = WebService.CLIENT.factory.create('EcAccountType')['CHECKING']
		record.Note = ""
		record.PaymentMethodID = None
		record.ClientID = None
		record.MerchantID = WebService.MERCHANT_ID
		record.IsDefault = False
		return record

	def __getattr__(self, name):
		if PaymentMethod.REQUIRE_COMPLIANCE:
			if name == 'note':
				return 	self._record.Note
			else:
				raise AttributeError("Compliance mode is turned on. Object has no attribute \'%s\'" % name)
		return self._data[name]

	def __setattr__(self, name, value):
		if '_record' not in self.__dict__ or self._record is None or PaymentMethod.REQUIRE_COMPLIANCE:
			if PaymentMethod.REQUIRE_COMPLIANCE and name == 'note':
				self._record.Note = value
			else:
				super(PaymentMethod, self).__setattr__(name, value)
		elif name not in dir(self):
			self._data[name] = value
		else:
			super(PaymentMethod, self).__setattr__(name, value)

	@property
	def id(self):
		return self._record.PaymentMethodID
	@property
	def account_holder(self):
		return self._record.AcctHolderName
	@account_holder.setter
	def account_holder(self, value):
		self._record.AcctHolderName = value
	@property
	def is_default(self):
		return self._record.IsDefault
	@is_default.setter
	def is_default(self, value):
		self._record.IsDefault = value

	def save(self):
		if self._client:
			self._record.ClientID = self._client.id
		if not PaymentMethod.REQUIRE_COMPLIANCE:
			enc = base64.b64encode(pickle.dumps(self._data))
			if six.PY3:
				enc = enc.decode('ascii')
			self._record.Note = enc
		if self.id is None:
			self._record.PaymentMethodID = 0
			self._record.PaymentMethodID = WebService.CLIENT.service['BasicHttpBinding_IClientService'].createPaymentMethod(self.authentication, self._record)
		else:
			self._record.EcAccountNumber = self._record.EcAccountTRN = ""
			self._record.PaymentMethodID = WebService.CLIENT.service['BasicHttpBinding_IClientService'].updatePaymentMethod(self.authentication, self._record)
		return self

	def delete(self):
		if self.id is not None:
			result = (WebService.CLIENT.service['BasicHttpBinding_IClientService'].deletePaymentMethod(self.authentication, WebService.MERCHANT_ID, self.id) == self.id)
			self._record.PaymentMethodID = None
		return self

	@staticmethod
	def retrieve(id, type, client_id=0):
		record = WebService.CLIENT.service['BasicHttpBinding_IClientService'].getPaymentMethod(WebService.get_authentication(WebService.CLIENT), WebService.MERCHANT_ID, client_id, id)
		if record == '':
			return None
		payment_method = type(record=record[0][0])
		return payment_method

	@staticmethod
	def find_all_by_client_id(id, bank_type, cc_type):
		methods = WebService.CLIENT.service['BasicHttpBinding_IClientService'].getPaymentMethod(WebService.get_authentication(WebService.CLIENT), WebService.MERCHANT_ID, id, 0)
		payment_objects = []
		if methods:
			for method in methods[0]:
				if method.CcCardNumber == "" or method.CcCardNumber is None:
					payment_method = bank_type(record=method)
				else:
					payment_method = cc_type(record=method)
				payment_objects.append(payment_method)
		return payment_objects

	def __str__(self):
		return str(self._record)
	
	def __repr__(self):
		return "<%s>" % str(self._record)

