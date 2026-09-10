import '../models/analysis/verified_snapshot.dart';
import '../models/genai/genai_explain_request.dart';
import '../models/ml_risk/diabetes_risk_request.dart';
import '../models/ml_risk/heart_disease_risk_request.dart';
import '../models/ml_risk/kidney_disease_risk_request.dart';
import '../models/ml_risk/risk_prediction_response.dart';
import '../models/reference/batch_analysis.dart';

/// Pure deterministic utility mapping verified clinical snapshots to backend API schemas.
///
/// SAFETY RULES:
/// - Never invent values or apply population averages.
/// - Never perform client-side imputation or scaling.
/// - Missing model features strictly remain null to allow backend to detect INSUFFICIENT_FEATURES.
class FeatureMapper {
  FeatureMapper._();

  static double? _toDouble(dynamic val) {
    if (val == null) return null;
    if (val is num) return val.toDouble();
    if (val is String) {
      final clean = val.trim().replaceAll(RegExp(r'[^0-9.-]'), '');
      return double.tryParse(clean);
    }
    return null;
  }

  static String _cleanName(String raw) {
    return raw
        .toLowerCase()
        .replaceAll(RegExp(r'[\s._\/\-]+'), ' ')
        .trim();
  }

  /// Maps verified snapshot to BatchAnalysisRequest for POST /api/v1/reference/analyze.
  static BatchAnalysisRequest toBatchAnalysisRequest(VerifiedSnapshot snapshot) {
    final ctx = snapshot.patientContext;
    return BatchAnalysisRequest(
      measurements: snapshot.measurements
          .map((m) => m.toMeasurementInput(forceVerified: true))
          .toList(),
      patientContext: (ctx.age != null || ctx.sex != null) ? ctx : null,
      reportId: null,
      persist: false,
    );
  }

  /// Maps verified snapshot to DiabetesRiskRequest (Pima Indians 8 features).
  static DiabetesRiskRequest toDiabetesRiskRequest(VerifiedSnapshot snapshot) {
    double? glucose;
    double? bloodPressure;
    double? insulin;
    double? bmi;
    double? skinThickness;
    double? pregnancies;
    double? pedigree;

    for (final m in snapshot.measurements) {
      final name = _cleanName(m.testName);
      final val = _toDouble(m.value);
      if (val == null) continue;

      if (name == 'glucose' ||
          name == 'blood glucose' ||
          name == 'fasting blood glucose' ||
          name == 'fbs' ||
          name == 'blood glucose fasting' ||
          name == 'fasting blood sugar' ||
          name == 'plasma glucose') {
        glucose = val;
      } else if (name == 'blood pressure' ||
          name == 'diastolic blood pressure' ||
          name == 'bp' ||
          name == 'diastolic bp') {
        bloodPressure = val;
      } else if (name == 'insulin' || name == 'serum insulin' || name == 'fasting insulin') {
        insulin = val;
      } else if (name == 'bmi' || name == 'body mass index') {
        bmi = val;
      } else if (name == 'skin thickness' || name == 'skinthickness' || name == 'triceps skin fold') {
        skinThickness = val;
      } else if (name == 'pregnancies' || name == 'pregnancy count') {
        pregnancies = val;
      } else if (name == 'diabetes pedigree function' || name == 'dpf' || name == 'pedigree') {
        pedigree = val;
      }
    }

    return DiabetesRiskRequest(
      pregnancies: pregnancies,
      glucose: glucose,
      bloodPressure: bloodPressure,
      skinThickness: skinThickness,
      insulin: insulin,
      bmi: bmi,
      diabetesPedigreeFunction: pedigree,
      age: snapshot.patientContext.age,
      isUserVerified: true,
      reportId: null,
    );
  }

  /// Maps verified snapshot to HeartDiseaseRiskRequest (Cleveland 13 features).
  static HeartDiseaseRiskRequest toHeartDiseaseRiskRequest(VerifiedSnapshot snapshot) {
    double? trestbps;
    double? chol;
    double? fbs;
    double? thalach;
    double? oldpeak;
    double? cp;
    double? restecg;
    double? exang;
    double? slope;
    double? ca;
    double? thal;

    for (final m in snapshot.measurements) {
      final name = _cleanName(m.testName);
      final val = _toDouble(m.value);
      if (val == null) continue;

      if (name == 'cholesterol' ||
          name == 'total cholesterol' ||
          name == 'serum cholesterol' ||
          name == 'chol' ||
          name == 't chol') {
        chol = val;
      } else if (name == 'glucose' ||
          name == 'fasting blood glucose' ||
          name == 'fbs' ||
          name == 'fasting blood sugar') {
        fbs = val > 120.0 ? 1.0 : 0.0;
      } else if (name == 'blood pressure' ||
          name == 'resting blood pressure' ||
          name == 'trestbps' ||
          name == 'bp' ||
          name == 'systolic blood pressure') {
        trestbps = val;
      } else if (name == 'maximum heart rate' ||
          name == 'max heart rate' ||
          name == 'thalach' ||
          name == 'heart rate') {
        thalach = val;
      } else if (name == 'chest pain type' || name == 'cp') {
        cp = val;
      } else if (name == 'resting ecg' || name == 'restecg') {
        restecg = val;
      } else if (name == 'exercise induced angina' || name == 'exang') {
        exang = val;
      } else if (name == 'st depression' || name == 'oldpeak') {
        oldpeak = val;
      } else if (name == 'st slope' || name == 'slope') {
        slope = val;
      } else if (name == 'colored vessels' || name == 'ca') {
        ca = val;
      } else if (name == 'thalassemia' || name == 'thal') {
        thal = val;
      }
    }

    // Sex encoding: 1.0 = Male, 0.0 = Female, null if unspecified
    double? sexNum;
    final s = snapshot.patientContext.sex?.trim().toUpperCase();
    if (s == 'M' || s == 'MALE') {
      sexNum = 1.0;
    } else if (s == 'F' || s == 'FEMALE') {
      sexNum = 0.0;
    }

    return HeartDiseaseRiskRequest(
      age: snapshot.patientContext.age,
      sex: sexNum,
      cp: cp,
      trestbps: trestbps,
      chol: chol,
      fbs: fbs,
      restecg: restecg,
      thalach: thalach,
      exang: exang,
      oldpeak: oldpeak,
      slope: slope,
      ca: ca,
      thal: thal,
      isUserVerified: true,
      reportId: null,
    );
  }

  /// Maps verified snapshot to KidneyDiseaseRiskRequest (UCI CKD 24 features).
  static KidneyDiseaseRiskRequest toKidneyDiseaseRiskRequest(VerifiedSnapshot snapshot) {
    double? bp;
    double? sg;
    double? al;
    double? su;
    double? bgr;
    double? bu;
    double? sc;
    double? sod;
    double? pot;
    double? hemo;
    double? pcv;
    double? wc;
    double? rc;

    String? rbc;
    String? pc;
    String? pcc;
    String? ba;
    String? htn;
    String? dm;
    String? cad;
    String? appet;
    String? pe;
    String? ane;

    for (final m in snapshot.measurements) {
      final name = _cleanName(m.testName);
      final numVal = _toDouble(m.value);
      final strVal = m.value?.toString().trim().toLowerCase();

      if (numVal != null) {
        if (name == 'serum creatinine' || name == 'creatinine' || name == 'sc' || name == 'cr') {
          sc = numVal;
        } else if (name == 'blood urea nitrogen' ||
            name == 'bun' ||
            name == 'blood urea' ||
            name == 'bu' ||
            name == 'urea') {
          bu = numVal;
        } else if (name == 'serum sodium' || name == 'sodium' || name == 'sod' || name == 'na') {
          sod = numVal;
        } else if (name == 'serum potassium' || name == 'potassium' || name == 'pot' || name == 'k') {
          pot = numVal;
        } else if (name == 'hemoglobin' || name == 'hb' || name == 'hgb' || name == 'hemo') {
          hemo = numVal;
        } else if (name == 'white blood cell count' || name == 'wbc' || name == 'tlc' || name == 'wc') {
          wc = numVal;
        } else if (name == 'glucose' ||
            name == 'fasting blood glucose' ||
            name == 'fbs' ||
            name == 'bgr' ||
            name == 'blood glucose random') {
          bgr = numVal;
        } else if (name == 'blood pressure' || name == 'bp') {
          bp = numVal;
        } else if (name == 'specific gravity' || name == 'sg') {
          sg = numVal;
        } else if (name == 'albumin' || name == 'al') {
          al = numVal;
        } else if (name == 'sugar' || name == 'su') {
          su = numVal;
        } else if (name == 'packed cell volume' || name == 'pcv') {
          pcv = numVal;
        } else if (name == 'red blood cell count' || name == 'rc') {
          rc = numVal;
        }
      }

      if (strVal != null) {
        if (name == 'red blood cells' || name == 'rbc') rbc = strVal;
        if (name == 'pus cell' || name == 'pc') pc = strVal;
        if (name == 'pus cell clumps' || name == 'pcc') pcc = strVal;
        if (name == 'bacteria' || name == 'ba') ba = strVal;
        if (name == 'hypertension' || name == 'htn') htn = strVal;
        if (name == 'diabetes mellitus' || name == 'dm') dm = strVal;
        if (name == 'coronary artery disease' || name == 'cad') cad = strVal;
        if (name == 'appetite' || name == 'appet') appet = strVal;
        if (name == 'pedal edema' || name == 'pe') pe = strVal;
        if (name == 'anemia' || name == 'ane') ane = strVal;
      }
    }

    return KidneyDiseaseRiskRequest(
      age: snapshot.patientContext.age,
      bp: bp,
      sg: sg,
      al: al,
      su: su,
      bgr: bgr,
      bu: bu,
      sc: sc,
      sod: sod,
      pot: pot,
      hemo: hemo,
      pcv: pcv,
      wc: wc,
      rc: rc,
      rbc: rbc,
      pc: pc,
      pcc: pcc,
      ba: ba,
      htn: htn,
      dm: dm,
      cad: cad,
      appet: appet,
      pe: pe,
      ane: ane,
      isUserVerified: true,
      reportId: null,
    );
  }

  /// Maps evaluated BatchAnalysisResponse to VerifiedAnalyteSummary items for GenAI explanation.
  static List<VerifiedAnalyteSummary> toVerifiedAnalyteSummaries(
    BatchAnalysisResponse referenceResponse,
  ) {
    final List<VerifiedAnalyteSummary> summaries = [];
    for (final r in referenceResponse.results) {
      summaries.add(
        VerifiedAnalyteSummary(
          testName: r.originalTestName,
          canonicalName: r.canonicalName,
          displayName: r.canonicalName ?? r.originalTestName,
          value: r.numericValue,
          unit: r.normalizedUnit ?? r.unit,
          classification: r.classification,
          referenceLow: r.referenceRange?.normalLow,
          referenceHigh: r.referenceRange?.normalHigh,
          referenceSource: r.referenceSource,
          analysisStatus: r.analysisStatus,
          warnings: r.warnings,
        ),
      );
    }
    return summaries;
  }

  /// Maps successful ML risk predictions (status == 'OK' and valid probability) to MLRiskSummary for GenAI.
  /// Strictly filters out INSUFFICIENT_FEATURES or errored predictions where probability is null.
  static List<MLRiskSummary> toMLRiskSummaries(
    List<RiskPredictionResponse> mlResponses,
  ) {
    final List<MLRiskSummary> summaries = [];
    for (final r in mlResponses) {
      if (r.status == 'OK' && r.riskProbability != null && r.riskBand != null) {
        summaries.add(
          MLRiskSummary(
            condition: r.condition,
            riskProbability: r.riskProbability!,
            riskBand: r.riskBand!,
            modelName: r.modelName,
            modelVersion: r.modelVersion,
            status: r.status,
          ),
        );
      }
    }
    return summaries;
  }
}
