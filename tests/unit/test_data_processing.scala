import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers
import org.scalatest.BeforeAndAfter
import scala.util.{Try, Success, Failure}
import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._
import org.apache.spark.sql.DataFrame

class DataProcessingTest extends AnyFlatSpec with Matchers with BeforeAndAfter {

  var spark: SparkSession = _
  
  before {
    spark = SparkSession.builder()
      .appName("DataProcessingTest")
      .master("local[*]")
      .getOrCreate()
  }

  after {
    spark.stop()
  }

  "DataTransformation" should "apply the correct transformations to the input data" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", 35, "Canada"),
      ("emily", 30, "UK")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val transformedDF = DataTransformation.transform(inputDF)

    val expectedData = Seq(
      ("NATE", 29, "USA"),
      ("PAUL", 35, "Canada"),
      ("EMILY", 30, "UK")
    ).toDF("name", "age", "country")

    assertDataFrameEquals(transformedDF, expectedData)
  }

  "DataCleaning" should "remove invalid rows from the dataset" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", -5, "Canada"),
      ("emily", 30, "UK"),
      (null, 25, "Germany")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val cleanedDF = DataCleaning.clean(inputDF)

    val expectedData = Seq(
      ("nate", 29, "USA"),
      ("emily", 30, "UK")
    ).toDF("name", "age", "country")

    assertDataFrameEquals(cleanedDF, expectedData)
  }

  "DataValidation" should "identify valid and invalid rows" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", -5, "Canada"),
      ("emily", 30, "UK"),
      (null, 25, "Germany")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val validationResults = DataValidation.validate(inputDF)

    validationResults._1.count() shouldEqual 2  // Valid records
    validationResults._2.count() shouldEqual 2  // Invalid records
  }

  "DataAggregation" should "correctly calculate average age per country" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", 35, "Canada"),
      ("emily", 30, "UK"),
      ("paul", 40, "Canada")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val aggregatedDF = DataAggregation.calculateAverageAge(inputDF)

    val expectedData = Seq(
      ("USA", 29.0),
      ("Canada", 37.5),
      ("UK", 30.0)
    ).toDF("country", "average_age")

    assertDataFrameEquals(aggregatedDF, expectedData)
  }

  "DataEnrichment" should "add region information based on country" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", 35, "Canada"),
      ("emily", 30, "UK")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val enrichedDF = DataEnrichment.enrichWithRegion(inputDF)

    val expectedData = Seq(
      ("nate", 29, "USA", "North America"),
      ("paul", 35, "Canada", "North America"),
      ("emily", 30, "UK", "Europe")
    ).toDF("name", "age", "country", "region")

    assertDataFrameEquals(enrichedDF, expectedData)
  }

  "DataFiltering" should "filter rows based on custom rules" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", 35, "Canada"),
      ("emily", 30, "UK"),
      ("matt", 25, "Australia")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val filteredDF = DataFiltering.filterByAgeAndCountry(inputDF, 30, "North America")

    val expectedData = Seq(
      ("paul", 35, "Canada")
    ).toDF("name", "age", "country")

    assertDataFrameEquals(filteredDF, expectedData)
  }

  def assertDataFrameEquals(actualDF: DataFrame, expectedDF: DataFrame): Unit = {
    assert(actualDF.schema.equals(expectedDF.schema))
    assert(actualDF.collect().sameElements(expectedDF.collect()))
  }

  "DataValidation" should "fail validation if any column contains null values" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", null, "Canada"),
      (null, 30, "UK")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val validationResult = DataValidation.validateNullChecks(inputDF)

    validationResult shouldEqual false
  }

  "DataTransformation" should "handle edge cases like empty DataFrames" in {
    import spark.implicits._

    val inputDF = Seq.empty[(String, Int, String)].toDF("name", "age", "country")

    val transformedDF = DataTransformation.transform(inputDF)

    transformedDF.count() shouldEqual 0
  }

  "DataProcessing" should "work end-to-end without errors" in {
    val inputData = Seq(
      ("nate", 29, "USA"),
      ("paul", 35, "Canada"),
      ("emily", 30, "UK")
    )

    import spark.implicits._

    val inputDF = inputData.toDF("name", "age", "country")

    val processedDF = DataProcessing.process(inputDF)

    processedDF.count() shouldEqual 3
  }

}