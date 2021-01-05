namespace JetsonNanoObjectClassificationWeb.Controllers
{
    using Azure.Storage.Blobs;
    using Azure.Storage.Blobs.Models;
    using JetsonNanoObjectClassificationWeb.Models;
    using Microsoft.AspNetCore.Mvc;
    using Microsoft.Extensions.Configuration;
    using Microsoft.Extensions.Logging;
    using System;

    public class ObjectClassificationController : Controller
    {
        private const string queueName = "jetson-nano-object-classification-requests";
        private const string containerName = "jetson-nano-object-classification-responses";

        private readonly ILogger<ObjectClassificationController> _logger;
        private readonly IConfiguration _configuration;
        private readonly string storageConnectionString = string.Empty;

        public ObjectClassificationController(ILogger<ObjectClassificationController> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            storageConnectionString = this._configuration.GetValue<string>("StorageConnectionString");
        }

        public IActionResult Index(string requestId, string className)
        {
            Guid requestGuid = new Guid(requestId);
            string imageUri = string.Empty;
            BlobContainerClient blobContainerClient = new BlobContainerClient(storageConnectionString, "jetson-nano-object-classification-responses");
            foreach (BlobItem blobItem in blobContainerClient.GetBlobs(BlobTraits.All))
            {
                if (blobItem != null && !string.IsNullOrEmpty(blobItem.Name) && blobItem.Name.Equals($"{requestId}/imageWithDetection.jpg", StringComparison.InvariantCultureIgnoreCase))
                {
                    imageUri = $"{blobContainerClient.Uri.AbsoluteUri}/{blobItem.Name}";
                }
            }

            ObjectClassificationModel objectClassificationModel = new ObjectClassificationModel()
            {
                ImageUri = new Uri(imageUri),
                RequestId = requestGuid,
                ClassName = className
            };

            return View(objectClassificationModel);
        }

        [HttpGet("HasImageUploaded")]
        [Route("objectclassification/{imageContainerGuid}/hasimageuploaded")]
        public JsonResult HasImageUploaded(string imageContainerGuid)
        {
            
            BlobContainerClient blobContainerClient = new BlobContainerClient(storageConnectionString, "jetson-nano-object-classification-responses");
            foreach(BlobItem blobItem in blobContainerClient.GetBlobs(BlobTraits.All))
            {
                if(blobItem != null && !string.IsNullOrEmpty(blobItem.Name) && blobItem.Name.Equals($"{imageContainerGuid}/imageWithDetection.jpg",StringComparison.InvariantCultureIgnoreCase))
                {
                    return new JsonResult($"{blobContainerClient.Uri.AbsoluteUri}/{blobItem.Name}");
                }
            }
            return new JsonResult(string.Empty);
        }
    }
}
