namespace JetsonNanoObjectClassificationWeb.Controllers
{
    using Azure.Storage.Queues; // Namespace for Queue storage types
    using JetsonNanoObjectClassificationWeb.Models;
    using Microsoft.AspNetCore.Mvc;
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

        public SendMessageController(ILogger<SendMessageController> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            storageConnectionString = this._configuration.GetValue<string>("StorageConnectionString");
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

            if(!userName.Equals(password, StringComparison.InvariantCultureIgnoreCase))
            {
                return View(null);
            }

            var objectClassificationModel = new ObjectClassificationModel()
            {
                ClassName = userName,
                RequestId = Guid.NewGuid(),
                ThresholdPercentage = 80
            };

            _ = QueueMessageAsync(objectClassificationModel, storageConnectionString);

            return View(objectClassificationModel);
        }


        public static async Task QueueMessageAsync(ObjectClassificationModel objectClassificationModel, string storageConnectionString)
        {
            string requestContent = $"{objectClassificationModel.RequestId}|{objectClassificationModel.ClassName}|{objectClassificationModel.ThresholdPercentage.ToString()}";


            // Instantiate a QueueClient which will be used to create and manipulate the queue
            QueueClient queueClient = new QueueClient(storageConnectionString, queueName);

            // Create the queue
            queueClient.CreateIfNotExists();

            if (queueClient.Exists())
            {
                Console.WriteLine($"Queue created: '{queueClient.Name}'");
                await queueClient.SendMessageAsync(requestContent);
            }
        }
    }
}
