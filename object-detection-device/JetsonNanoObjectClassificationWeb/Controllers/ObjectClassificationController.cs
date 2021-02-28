namespace JetsonNanoObjectClassificationWeb.Controllers
{
    using Azure.Storage.Blobs;
    using Azure.Storage.Blobs.Models;
    using JetsonNanoObjectClassificationWeb.Models;
    using Microsoft.AspNetCore.Mvc;
    using Microsoft.Extensions.Configuration;
    using Microsoft.Extensions.Logging;
    using System;
    using System.Threading.Tasks;
    using System.Collections.Generic;

    public class ObjectClassificationController : Controller
    {
        private const string queueName = "iot-edge-object-classification-requests";
        private const string containerName = "iot-edge-object-classification-responses";
        private const string imageWithDetection = "imageWithDetection.jpg";

        private readonly ILogger<ObjectClassificationController> _logger;
        private readonly IConfiguration _configuration;
        private readonly string storageConnectionString = string.Empty;

        public ObjectClassificationController(ILogger<ObjectClassificationController> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            storageConnectionString = this._configuration.GetValue<string>("StorageConnectionString");
        }

        public async Task<IActionResult> Index(string requestId, string className)
        {
            string imageUri = string.Empty;
            Guid requestGuid = default(Guid);
            if (Guid.TryParse(requestId, out requestGuid))
            {
                BlobContainerClient blobContainerClient = new BlobContainerClient(storageConnectionString, containerName);

                await foreach (BlobItem blobItem in blobContainerClient.GetBlobsAsync(BlobTraits.All))
                {
                    if (string.Equals(blobItem?.Name, $"{requestId}/{imageWithDetection}", StringComparison.InvariantCultureIgnoreCase))
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

            return View(null);
        }

        [HttpGet("HasImageUploaded")]
        [Route("objectclassification/{imageContainerGuid}/hasimageuploaded")]
        public JsonResult HasImageUploaded(string imageContainerGuid)
        {
            
            BlobContainerClient blobContainerClient = new BlobContainerClient(storageConnectionString, "iot-edge-object-classification-responses");
            foreach(BlobItem blobItem in blobContainerClient.GetBlobs(BlobTraits.All))
            {
                if (string.Equals(blobItem?.Name, $"{imageContainerGuid}/{imageWithDetection}", StringComparison.InvariantCultureIgnoreCase))
                {
                    return new JsonResult($"{blobContainerClient.Uri.AbsoluteUri}/{blobItem.Name}");
                }
            }
            return new JsonResult(string.Empty);
        }
    }
}
