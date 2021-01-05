namespace JetsonNanoObjectClassificationWeb.Controllers
{
    using System;
    using System.Collections.Generic;
    using System.Diagnostics;
    using System.Linq;
    using System.Threading.Tasks;
    using Microsoft.AspNetCore.Mvc;
    using Microsoft.Extensions.Logging;
    using JetsonNanoObjectClassificationWeb.Models;
    using Azure.Messaging.EventHubs.Producer;
    using Azure.Messaging.EventHubs;
    using Azure.Storage.Queues; // Namespace for Queue storage types
    using Azure.Storage.Queues.Models; // Namespace for PeekedMessage
    using System.Text;
    using Microsoft.Extensions.Configuration;
    using Microsoft.AspNetCore.Http;

    public class HomeController : Controller
    {
        private const string queueName = "jetson-nano-object-classification-requests";

        private readonly ILogger<HomeController> _logger;
        private readonly IConfiguration _configuration;

        public HomeController(ILogger<HomeController> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
        }

        public IActionResult Index()
        {
            return View();
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
