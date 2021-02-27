namespace JetsonNanoObjectClassificationWeb.Models
{
    using System;

    public class ObjectClassificationModel
    {
        public Guid RequestId { get; set; }

        public string ClassName { get; set; }

        public int ThresholdPercentage { get; set; }

        public Uri ImageUri { get; set; }
    }
}
