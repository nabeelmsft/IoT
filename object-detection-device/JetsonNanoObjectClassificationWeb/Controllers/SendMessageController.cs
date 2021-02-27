namespace JetsonNanoObjectClassificationWeb.Controllers
{
    using Azure.Storage.Queues; // Namespace for Queue storage types
    using JetsonNanoObjectClassificationWeb.Models;
    using Microsoft.AspNetCore.Mvc;
    using Microsoft.Azure.Devices;
    using Microsoft.Extensions.Configuration;
    using Microsoft.Extensions.Logging;
    using System;
    using System.Threading.Tasks;

    public class SendMessageController : Controller
    {
        private const string queueName = "jetson-nano-object-classification-requests";

        private readonly ILogger<SendMessageController> _logger;
        private readonly IConfiguration _configuration;
        private readonly string storageConnectionString = string.Empty;
        private static ServiceClient _serviceClient;
        private readonly string iotHubConnectionString = string.Empty;

        public SendMessageController(ILogger<SendMessageController> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            storageConnectionString = this._configuration.GetValue<string>("StorageConnectionString");
            iotHubConnectionString = this._configuration.GetValue<string>("IoTHubConnectionString");
        }

        [HttpPost("sendmessage")]
        public IActionResult Index()
        {
            string userName = string.Empty;
            string password = string.Empty;

            if (!string.IsNullOrEmpty(Request.Form["userName"]))
            {
                userName = Request.Form["userName"];
            }

            if (!string.IsNullOrEmpty(Request.Form["password"]))
            {
                password = Request.Form["password"];
            }

            // Simulation of first factor authentication presented here.
            // For real world example visit https://docs.microsoft.com/azure/app-service/overview-authentication-authorization
            if (!userName.Equals(password, StringComparison.InvariantCultureIgnoreCase))
            {
                return View(null);
            }

            var objectClassificationModel = new ObjectClassificationModel()
            {
                ClassName = userName,
                RequestId = Guid.NewGuid(),
                ThresholdPercentage = 70
            };

            _serviceClient = ServiceClient.CreateFromConnectionString(iotHubConnectionString);
            _ = InvokeMethod(objectClassificationModel);

            return View(objectClassificationModel);
        }

        // Invoke the direct method on the device, passing the payload
        private static async Task InvokeMethod(ObjectClassificationModel objectClassificationModel)
        {
            try
            {
                var methodInvocation = new CloudToDeviceMethod("ProcessRequest") { ResponseTimeout = TimeSpan.FromSeconds(30) };
                var jsonPayload = "{\"CoorelationId\": \"" + objectClassificationModel.RequestId + "\", \"ClassName\": \"" + objectClassificationModel.ClassName + "\", \"ThresholdPercentage\": \"" + objectClassificationModel.ThresholdPercentage.ToString() + "\"}";

                methodInvocation.SetPayloadJson(jsonPayload);

                // Invoke the direct method asynchronously and get the response from the simulated device.
                var response = await _serviceClient.InvokeDeviceMethodAsync("object-detection-device", "ObjectDetectionDeviceModule", methodInvocation);
            }
            catch(Exception exception)
            {
                Console.WriteLine(exception);
            }
        }
    }
}
